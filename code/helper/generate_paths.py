import json

# Replace the element with a row from Json file, then execute the script to print all json paths

element = ''
table_name = 'notifications'

element  = ''
table_name = 'job'

element = ''
table_name = 'legend_version'

element = ''
table_name = 'job_event'


def get_json_paths(element):

    def analyze_field(parent, key, value, level, parent_path):
        path = '{}__{}'.format(parent_path, key) if parent_path else '{}'.format(key)

        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) or isinstance(item, list):
                    analyze_field(parent, key, item, level + 1, parent_path)

        if isinstance(value, dict):
            for k, v in value.items():
                print('{}__{}'.format(path, k))
                analyze_field(value, k, v, level + 1, path)

    for field_key, field_value in element.items():
        analyze_field(element, field_key, field_value, 1, None)

    return element


element = json.loads(element)
get_json_paths(element)

print (element)







