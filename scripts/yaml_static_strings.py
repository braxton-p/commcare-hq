import argparse
import yaml

parser = argparse.ArgumentParser(
    description='''
    Convert a yaml file for static analyzable strings

    Example:
    python scripts/yaml_static_strings.py -f corehq/apps/app_manager/static/app_manager/json/commcare-app-settings.yaml --fields name description value_names disabled_txt values_txt
    '''
)

parser.add_argument(
    '-f',
    '--file',
    help='YAML file to parse',
    required=True,
)
parser.add_argument(
    '--fields',
    nargs='+',
    required=True,
    help='Fields to extract',
)

parser.add_argument(
    '--prefix',
    nargs='+',
    required=False,
    default='gettext_noop',
    help='Fields to extract',
)


def format_string(value, prefix):
    return "{}('{}'),".format(prefix, value.replace("'", "\\'"))


if __name__ == "__main__":
    args = parser.parse_args()
    yaml_filename = args.file
    fields = args.fields
    prefix = args.prefix
    output = []

    with open(yaml_filename, 'r', encoding='utf-8') as f:
        doc = yaml.safe_load(f)

    for entry in doc:
        for key, value in entry.items():
            if key in fields:
                if not isinstance(value, str):
                    for v in value:
                        output.append(format_string(v, prefix))
                else:
                    output.append(format_string(value, prefix))

    for value in output:
        print(value)
