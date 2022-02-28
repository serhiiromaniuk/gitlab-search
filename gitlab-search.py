#!/usr/bin/python3
import gitlab
import sys
import argparse
import re

def eprint(*args, **kwargs):
    # https://stackoverflow.com/a/14981125
    print(*args, file=sys.stderr, **kwargs)

def search(
        gitlab_server, token, file_filter, text, group=None, project_filter=None,
        api_debug=False, internal_debug=False, filename_regex=False,
        output_match=False, output_path=False, output_ssh_url=False
    ):
    return_value = []
    
    gl = gitlab.Gitlab(gitlab_server, private_token=token)
    if api_debug:
        gl.enable_debug()

    filter_groups   = not (group == '' or group==None)
    filter_projects = not (project_filter == '' or project_filter==None)

    if not filter_groups and not filter_projects:
        projects = gl.projects.list(all=True)
    else:
        projects     = []
        group_object = gl.groups.get(group)

        if filter_projects:
            group_projects = group_object.projects.list(search=project_filter, include_subgroups=True)
        else:
            group_projects = group_object.projects.list(all=True, include_subgroups=True)
            
        for group_project in group_projects:
            projects.append(gl.projects.get(group_project.id))

    if internal_debug:
        eprint("Number of projects that will be searched:", len(projects))


    for project in projects:
        if internal_debug:
            if hasattr(project, 'path'):
                path = project.path
            else:
                path = project.name
            eprint("Project: ",path)

        files = []
        try:
            files = project.repository_tree(recursive=True, all=True)
        except Exception as e:
            print(str(e), "Error getting tree in project:", project.name)

        for file in files:
            if internal_debug:
                fpath = file.get('path',None) if file.get('path',None) != None else file.get('name',None)
                eprint("  File: ", fpath)

            if filename_regex:
                matches          = re.findall(file_filter, file['name'])
                filename_matches = len(matches) > 0
            else:
                filename_matches = file_filter == file['name']
            
            if filename_matches:
                file_content = str(project.files.raw(file_path=file['path'], ref='master')).split("\\n")

                for line in file_content:
                    if text in line:
                        value = {
                            "project": project.name,
                            "file": file['path']
                        }
                        if output_match: value["match"] = line
                        if output_path: value["path"] = project.namespace["full_path    "]
                        if output_ssh_url: value["ssh_url"] = project.ssh_url_to_repo
                        return_value.append(value)
    return return_value

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-debug",         action="store_true", help="Show all API calls")
    parser.add_argument("--internal-debug",    action="store_true", help="Show all iterated items and other dubugv info")
    parser.add_argument("--filename-is-regex", action="store_true", help="FILE_FILTER become Python regular expressions, so it can be '.*\.cpp' to search for all files with extension cpp")
    parser.add_argument("--output-match",      action="store_true", help="Output matching line")
    parser.add_argument("--output-path",       action="store_true", help="Output full project path")
    parser.add_argument("--output-ssh-url",    action="store_true", help="Output SSH repo url for clone")
    parser.add_argument("GITLAB_SERVER",       nargs=1,             help="URL of Gitlab server, eg. https://gitlab.com/")
    parser.add_argument("GITLAB_USER_TOKEN",   nargs=1,             help="Access token with api_read access")
    parser.add_argument("FILE_FILTER",         nargs=1,             help="Filter for filenames to search in")
    parser.add_argument("TEXT_TO_SEARCH",      nargs=1,             help="Text to find in files")
    parser.add_argument("GROUP",               nargs='?',           help="Group to search for projects in, can be subgroup eg. parent_group/subgroup/another_subgroup")
    parser.add_argument("PROJECT_FILTER",      nargs='?',           help="Filter for project names to look into")
    args = parser.parse_args()

    api_debug_arg      = args.api_debug
    internal_debug_arg = args.internal_debug
    regex_arg          = args.filename_is_regex
    output_match_arg   = args.output_match
    output_path_arg    = args.output_path
    output_ssh_url_arg = args.output_ssh_url
    gitlab_server_arg  = args.GITLAB_SERVER[0]
    token_arg          = args.GITLAB_USER_TOKEN[0]
    file_filter_arg    = args.FILE_FILTER[0]
    text_arg           = args.TEXT_TO_SEARCH[0]
    group_arg          = None if args.GROUP          == None else args.GROUP
    project_filter_arg = None if args.PROJECT_FILTER == None else args.PROJECT_FILTER

    print(
        search(
            gitlab_server_arg, token_arg, file_filter_arg, text_arg, group_arg,
            project_filter_arg, api_debug_arg, internal_debug_arg, regex_arg,
            output_match_arg, output_path_arg, output_ssh_url_arg
        )
    )
