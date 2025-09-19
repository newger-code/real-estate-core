#!/usr/bin/env python3
"""
Fix indentation issues in scrape_property.py
All class methods should be indented 4 spaces from class definition
"""

def fix_scrape_property_indentation():
    """Fix the indentation issues in scrape_property.py"""

    # Read the original file
    with open('../scrape_property.py', 'r') as f:
        lines = f.readlines()

    # Find methods that should be class methods but aren't properly indented
    method_patterns = [
        'async def scrape_homes_com(self, page):',
        'async def extract_homes_property_data(self, page):',
        'async def scrape_redfin(self, page):',
        'async def extract_redfin_property_data(self, page):',
        'async def run(self):'
    ]

    fixed_lines = []
    in_class = False
    in_method = False
    method_indent_level = 0

    for i, line in enumerate(lines):
        # Track if we're inside the PropertyScraper class
        if line.strip().startswith('class PropertyScraper:'):
            in_class = True
            fixed_lines.append(line)
            continue

        # Check if we've left the class (reached global function)
        if in_class and line.strip().startswith('async def main()'):
            in_class = False

        # Handle class methods that need fixing
        if in_class:
            stripped = line.strip()

            # Check if this is a method that should be indented
            is_target_method = any(pattern in stripped for pattern in method_patterns)

            if is_target_method and not line.startswith('    '):
                # This method needs to be indented as a class method
                in_method = True
                method_indent_level = 1
                fixed_lines.append('    ' + line.lstrip())
                continue

            elif in_method and line.strip() == '':
                # Empty line in method
                fixed_lines.append(line)
                continue

            elif in_method and not line.strip().startswith('#') and line.strip() != '':
                # Method content - needs to be indented relative to method definition
                current_indent = len(line) - len(line.lstrip())

                # If the current line has less than 4 spaces and contains content,
                # it's probably method content that needs fixing
                if current_indent < 4 and line.strip():
                    # Add proper indentation (4 spaces for method + existing relative indent)
                    additional_indent = 4
                    if current_indent > 0:
                        additional_indent += current_indent
                    fixed_lines.append(' ' * additional_indent + line.lstrip())
                else:
                    fixed_lines.append(line)
                continue

            elif in_method and (line.strip().startswith('async def ') or line.strip().startswith('def ')):
                # Start of next method
                in_method = False
                if not line.startswith('    ') and 'self' in line:
                    fixed_lines.append('    ' + line.lstrip())
                else:
                    fixed_lines.append(line)
                continue

        fixed_lines.append(line)

    # Write the fixed version
    with open('../scrape_property_fixed.py', 'w') as f:
        f.writelines(fixed_lines)

    print("✅ Fixed indentation issues")
    print("✅ Created scrape_property_fixed.py")

    return '../scrape_property_fixed.py'

if __name__ == '__main__':
    fix_scrape_property_indentation()