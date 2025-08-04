#!/usr/bin/python3
import os
import re
import sys
from collections import defaultdict
from natsort import natsorted

version_regex = re.compile(r"VERSIONS\s*=\s*(.*)$")
docker_file_regex = re.compile(r"(?<=Dockerfile\.).+")
exclude_file_regex = re.compile(r"(?<=\.exclude-).+")

table_regex = re.compile(r"(<!--\nTable start\n-->\n).*(<!--\nTable end\n-->\n)", re.DOTALL)

# gets the versions of the container from the Makefile
def _get_versions():
    try:
        makefile = open('Makefile', 'r')
    except Exception as e:
        print(f"An exception occured when trying to read the Makefile: {e}", file=sys.stderr)
        exit(1)
    for line in makefile.readlines():
        match = re.search(version_regex, line)
        if match:
            return match.group(1).split(" ")

# generates the table string
def _create_table(distros, versions):
    table = ""
    # prints the distros header
    table += f"||{'|'.join(distros)}|\n"
    # prints the table column separator
    # alliging the verions to left and ticks to center
    table += f"|:--|{':--:|' * len(distros)}\n"
    for version in versions:
        # prints the version line header
        table += f"|{version}"
        # goes over the distros and prints a tick if it is in the
        # docker files and not in the exclude files
        for distro in distros:
            table += '|'
            if distro in docker_distros[version] and not distro in exclude_distros[version]:
                table += '✓'
        # end the table line
        table += '|\n'
    return table

# reads the README.md, finds the Table start and Table end comments
# replaces any string between them with the table string
# and writes it back to the README.md file
def _replace_in_readme(table):
    try:
        readme = open("README.md", "r")
    except Exception as e:
        print(f"An error occured while trying to read README.md: {e}", file=sys.stderr)
        exit(1)
    original_readme = readme.read()

    if not re.search(table_regex, original_readme):
        print("The Table start and Table end tag was not found, not modifying README.md", file=sys.stderr)
        exit(0)

    new_readme = re.sub(table_regex, f"\\1{table}\\2", original_readme)
    try:
        readme = open("README.md", "w")
    except Exception as e:
        print(f"An error occured while trying to write to README.md: {e}", file=sys.stderr)
        exit(1)
    readme.write(new_readme)

if __name__ == "__main__":
    exclude_distros = defaultdict(list)
    docker_distros = defaultdict(list)

    versions = _get_versions()

    if not versions:
        print("No versions found in the Makefile, please make sure the syntax is correct", file=sys.stderr)
        exit(2)

    # goes through all the versions and gets their dockerfile
    # and exclude- distros
    for version in versions:
        files = os.listdir(version)
        exclude_distros[version] = [match.group(0) for s in files if (match := re.search(exclude_file_regex, s))]
        docker_distros[version] = [match.group(0) for s in files if (match := re.search(docker_file_regex, s))]

    # gets the sorted unique distro values from the flattened
    # docker_distros values
    distros = natsorted(set([s for value_list in docker_distros.values() for s in value_list]))

    table = _create_table(distros, versions)
    _replace_in_readme(table)
