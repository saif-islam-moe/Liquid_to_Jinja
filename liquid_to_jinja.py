import re

def convert_capture_to_set(match):
    variable_name = match.group(1).strip()
    content = match.group(2).strip()
    return f"{{% set {variable_name} %}}{content}{{% endset %}}"

def convert_number_with_delimiter(match):
    liquid_variable = match.group(1).strip()
    liquid_variable2 = match.group(2).strip()
    return f"{{% set {liquid_variable} = '{{:,}}'.format({liquid_variable2}) %}}"

def convert_unless_to_if_not(match):
    condition = match.group(1).strip()
    # Convert the 'contains' condition into an 'in' or 'not in' condition
    condition = re.sub(r'(\w+)\s+contains\s+(.*)', r"\2 not in \1", condition)
    contents = match.group(2).strip()
    return f"{{% if {condition} %}}{contents}{{% endif %}}"

def convert_case_to_if_elif(match):
    case_variable = match.group(1).strip()
    contents = match.group(2).strip()
    when_clauses = re.split(r'{%\s*when\s+(.*?)\s*%}', contents)
    when_clauses = [w.strip() for w in when_clauses if w.strip()]
    else_clause = re.search(r'{%\s*else\s*%}(.+?){%\s*endcase\s*%}', contents, re.DOTALL)
    jinja_clauses = []
    for i in range(len(when_clauses)//2):
        condition = when_clauses[i*2].strip("'\"")
        jinja_clauses.append(f"{{% elif {case_variable} == {condition} %}}{when_clauses[i*2+1]}")
    if jinja_clauses:
        jinja_clauses[0] = jinja_clauses[0].replace('elif', 'if', 1)
    if else_clause:
        jinja_clauses.append(f"{{% else %}}{else_clause.group(1)}")
    jinja_clauses.append("{% endif %}")
    return '\n'.join(jinja_clauses)

def convert_variables_in_conditions(match):
    keyword = match.group(1)
    condition = match.group(2)
    condition = re.sub(r'\{\{\${(\w+)}\}\}', r'\1', condition) # Keep variable placeholders for later Jinja conversion
    return f'{{% {keyword} {condition} %}}'

def convert_variables_in_loops(match):
    loop_variable = match.group(1)
    iterable = match.group(2)
    iterable = re.sub(r'\{\{\${(\w+)}\}\}', r'{{ \1 }}', iterable) # Keep variable placeholders for later Jinja conversion
    return f'{{% for {loop_variable} in {iterable} %}}'

def remove_inner_double_curly_braces(match):
    text_inside = match.group(0)
    cleaned_text = re.sub(r'\{\{(.*?)\}\}', r'\1', text_inside)
    return cleaned_text

def convert_replace_filter(match):
    variable = match.group(1)
    old_string = match.group(2).replace('"', '')
    print(old_string)
    new_string = match.group(3).replace('"', '')
    return f"{{% set {variable} = {variable} | replace('{old_string}', '{new_string}') %}}"

# Add this new function inside your existing script
def convert_dot_first_to_index_zero(match):
    variable_name = match.group(1).strip()
    variable_name1 = match.group(2).strip()
    return f"{{% set {variable_name} = {variable_name1}[0] %}}"

def convert_increment_decrement(match):
    operation = "set"  # Default to set for increment and decrement
    variable_name = match.group(1).strip()
    if match.group(0).startswith("{% increment"):
        return f"{{% {operation} {variable_name} = {variable_name} + 1 %}}"
    elif match.group(0).startswith("{% decrement"):
        return f"{{% {operation} {variable_name} = {variable_name} - 1 %}}"
    return match.group(0) # Fallback if not increment or decrement

def convert_string_filters(match):
    print("here")
    variable = match.group(1)
    filter_name = match.group(2)
    filter_args = match.group(3) if match.group(3) else ''
    if filter_name == 'downcase':
        return f"{{{{ {variable}|lower }}}}"
    elif filter_name == 'upcase':
        return f"{{{{ {variable}|upper }}}}"
    elif filter_name == 'capitalize':
        return f"{{{{ {variable}|capitalize }}}}"
    elif filter_name == 'strip':
        return f"{{{{ {variable}|trim }}}}" # Jinja 'trim' is similar to Liquid 'strip'
    elif filter_name == 'escape':
        return f"{{{{ {variable}|e }}}}" # Jinja 'e' is the escape filter
    elif filter_name == 'url_encode':
        return f"{{{{ {variable}|urlencode }}}}"
    elif filter_name == 'newline_to_br':
        return f"{{{{ {variable}|replace('\\n', '<br>')|safe }}}}" # Basic replacement, consider better HTML generation if needed
    # elif filter_name == 'replace':
        # print("here")
        # filter_args = match.group(3).strip() if match.group(3) else ''
        # print(filter_args)
        # if filter_name == 'replace':
        #     parts = re.split(r",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", filter_args)
        #     if len(parts) >= 2:
        #         old_str = parts[0].strip().strip("'\"")
        #         new_str = parts[1].strip().strip("'\"")
        #         return f"{{{{ {variable}|replace('{old_str}', '{new_str}') }}}}"
        # old_string = match.group(2).replace('"', '')
        # new_string = match.group(3).replace('"', '')
        # return f"{{% set {variable} = {variable} | replace('{old_string}', '{new_string}') %}}"
    elif filter_name == 'slice':
        slice_arg = match.group(3).strip()
        if slice_arg:
            parts = [part.strip() for part in slice_arg.split(',')]
            if len(parts) == 2:
                start, length = parts
                return f"{{{{ {variable}[{start}:{int(start) + int(length)}] }}}}" # Python slicing
    variable = match.group(1)
    filter_name = match.group(2)
    filter_args = match.group(3) if match.group(3) else ''
    
    if filter_name == 'remove':
        remove_arg = filter_args.strip().strip('"')  # Remove any double quotes around the argument
        # Escape single quotes correctly
        if remove_arg == "'":
            return f'{{{{ {variable}|replace("{remove_arg}", "") }}}}'
        else:
            return f"{{{{ {variable}|replace('{remove_arg}', '') }}}}"
    return match.group(0) # Fallback if filter not handled

def replace_hyphens_with_underscores(input_string):
    # Replace hyphens with underscores in variables after 'assign' or 'set'
    pattern_assign_set = r'({%\s*(assign|set)\s+[\w]*\w)-([\w]+\s*=)'
    replaced_string = re.sub(pattern_assign_set, lambda match: f"{match.group(1)}_{match.group(3)}", input_string)
    
    # Replace hyphens with underscores in variable names inside double curly braces
    pattern_double_curly = r'({{[\s]*[\w]+)-([\w]+[\s]*}})'
    replaced_string = re.sub(pattern_double_curly, lambda match: f"{match.group(1)}_{match.group(2)}", replaced_string)
    
    # Replace hyphens with underscores in utm_content parameter value in URLs, avoiding hrefs
    pattern_utm_content = r'(https?://[^ \t\n\r\f\v"\'<]+?utm_content=)([^&]*\w)-(\w+)'
    replaced_string = re.sub(pattern_utm_content, lambda match: f"{match.group(1)}{match.group(2)}_{match.group(3)}", replaced_string)
    
    return replaced_string


def convert_liquid_to_jinja(liquid_template):
    # Convert comments
    jinja_template = re.sub(r'{%-?\s*comment\s*-?%}(.+?){%-?\s*endcomment\s*-?%}', r'{# \1 #}', liquid_template, flags=re.DOTALL)

    # Convert increment and decrement
    jinja_template = re.sub(r'{%\s*(increment|decrement)\s+(\w+)\s*%}', convert_increment_decrement, jinja_template)
    # Convert conditions (if, elsif, else)
    jinja_template = re.sub(r'{%\s*(if|elsif)\s+(.*?)\s*%}', convert_variables_in_conditions, jinja_template)
    jinja_template = re.sub(r'{%\s*else\s*%}', '{% else %}', jinja_template) # Simple else conversion

    # Convert loops
    jinja_template = re.sub(r'{%\s*for\s+(.*?)\s*in\s+(.*?)\s*%}', convert_variables_in_loops, jinja_template)

    # **NEW: Convert set with string slicing**
    jinja_template = re.sub(r'{%\s*set\s+(\w+)\s*=\s*(\w+\.\w+)\s*\[:(\d+)\]\s*%}', r'{% set \1 = \2[:\3] %}', jinja_template)

    # Convert the multiply (`times`) filter
    jinja_template = re.sub(r'{%\s*assign\s+(\w+)\s*=\s*(\d+)\s*\|\s*times:\s*(\d+)\s*%}', r'{% set \1 = \2 * \3 %}', jinja_template)

    # Convert the truncate filter with indices first
    jinja_template = re.sub(r'{{\s*(\w+)\[(\d+)\]\s*\|\s*truncate:\s*(\d+)\s*}}', r'{{ \1[\2][:\3] }}', jinja_template)

    # Convert the truncate filter without indices
    jinja_template = re.sub(r'{{\s*(\w+)\s*\|\s*truncate:\s*(\d+)\s*}}',  r'{{ \1[:\2] }}', jinja_template)

    # Convert the split filter
    jinja_template = re.sub(r'{{\s*(\w+)\[(\d+)\]\s*\|\s*split\s*:\s*"([^"]+)"\s*}}', r'{{ \1[\2].split("\3") }}', jinja_template)
    jinja_template = re.sub(r'{{\s*(\w+)\s*\|\s*split\s*:\s*"([^"]+)"\s*}}', r'{{ \1.split("\2") }}', jinja_template)

    # Convert custom_attribute.${variable_name}
    jinja_template = re.sub(r'\{\{\s*custom_attribute\.\$\{(\w+)\}\s*\}\}', r"{{ UserAttribute['\1'] }}", jinja_template)
    jinja_template = re.sub(r'\{\{\s*campaign\.\$\{name\}\s*\}\}',r"{{ CampaignAttribute['c_n'] }}",jinja_template)
    jinja_template = re.sub(r'\{\{\s*content_blocks\.\$\{(\w+)\}\s*\}\}',r"{{ ContentBlock['\1'] }}",jinja_template)


    # Convert string filters (downcase, upcase, capitalize, strip, escape, url_encode, newline_to_br, replace, remove, slice)
    jinja_template = re.sub(r'\{\{\s*(\w+)\s*\|\s*(downcase|upcase|capitalize|strip|escape|url_encode|newline_to_br|replace|remove|slice)(?::(.*?))?\s*\}\}', convert_string_filters, jinja_template)

    jinja_template = re.sub(r"{%\s*set\s+(\w+)\s*=\s*(\w+)\.first\s*%}", convert_dot_first_to_index_zero, jinja_template )

    # Convert general assign statements; this should be placed after the specific times and truncate ones
    jinja_template = re.sub(r'{%\s*assign\s+(\w+)\s*=(.*?)\s*%}', r'{% set \1 = \2 %}', jinja_template)

    # Convert case and capture blocks
    jinja_template = re.sub(r'{%\s*case\s+(.*?)\s*%}(.*?){%\s*endcase\s*%}', convert_case_to_if_elif, jinja_template, flags=re.DOTALL)
    jinja_template = re.sub(r'{%\s*capture\s+(\w+)\s*%}(.+?){%\s*endcapture\s*%}', convert_capture_to_set, jinja_template, flags=re.DOTALL)

    # Clean up variable references
    jinja_template = re.sub(r'{{\s*(\w+)\s*}}', r'{{ \1 }}', jinja_template)


    # Fallback conversion for truncate filters (keep this as it worked)
    jinja_template = re.sub(r'\|\s*truncate:\s*(\d+)\s*%}', r'[:\1] %}', jinja_template)

    # Broader fallback conversion for any remaining assign statements
    jinja_template = re.sub(r'{%\s*assign\s+(.*?)\s*%}', r'{% set \1 %}', jinja_template)

    # Fallback for removing only {{ and }} inside {% ... %}
    jinja_template = re.sub(r'({%\s*.*?)(\{\{(.*?)\}\})(.*?\s*%})', r'\1\3\4', jinja_template)

    # Fallback for removing all {{ and }} inside {% ... %}
    jinja_template = re.sub(r'{%.*?%}', remove_inner_double_curly_braces, jinja_template, flags=re.DOTALL)

    # Removal of | append: ""
    jinja_template = re.sub(r'\|\s*append:\s*""', '', jinja_template)

    # Removal of {% break %}
    jinja_template = re.sub(r'{%\s*break\s*%}', '', jinja_template)

    jinja_template = re.sub(r'{{\s*(\S+)\s*\|\s*truncate:\s*(\d+)\s*}}', r'{{ \1[:\2] }}', jinja_template)

    jinja_template = re.sub(r'{%\s*unless\s+(.*?)\s*%}(.*?){%\s*endunless\s*%}', convert_unless_to_if_not, jinja_template, flags=re.DOTALL)

    jinja_template = re.sub(
        r"{%\s*set\s+(\w+)\s*=\s*([\w\.]+)\s*\|\s*replace:\s*'(.*?)'\s*,\s*'(.*?)'\s*%}",
        r"{% set \1 = \2 | replace('\3', '\4') %}",
        jinja_template
    )

    jinja_template = re.sub(
        r"{%\s*set\s+(\w+)\s*=\s*(\w+)\s*\|\s*number_with_delimiter\s*%}",
        convert_number_with_delimiter,
        jinja_template
    )

    jinja_template = re.sub(
        r"{%\s*set\s+(\w+)\s*=\s*([\w\.]+)\s*\|\s*split:\s*'(\S+)'\s*%}",
        r"{% set \1 = \2.split('\3') %}",
        jinja_template
    )

    jinja_template = re.sub(
        r"{%\s*set\s+(\w+)\s*=\s*([\w\.]+)\s*\|\s*times:\s*(\d+)\s*%}",
        r"{% set \1 = \2*\3 %}",
        jinja_template
    )

    jinja_template = re.sub(
        r"{{\s*(.*?)\s*\|\s*plus:\s*(\d+)\s*}}",
        r"{{ \1 + \2 }}",
        jinja_template
    )

    jinja_template = replace_hyphens_with_underscores(jinja_template)

    # Ensure final value is a string
    return jinja_template or ''
