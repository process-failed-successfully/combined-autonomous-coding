import sys
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from shared.dependencies import DependencyAnalyzer

class LicenseLabManager:
    """Manages License Lab operations: generating and checking licenses."""

    LICENSES: Dict[str, Dict[str, Any]] = {
        "mit": {
            "name": "MIT License",
            "description": "A short and simple permissive license with conditions only requiring preservation of copyright and license notices.",
            "permissions": ["Commercial use", "Modification", "Distribution", "Private use"],
            "conditions": ["License and copyright notice"],
            "limitations": ["Liability", "Warranty"],
            "template": """MIT License

Copyright (c) [year] [fullname]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
        },
        "apache-2.0": {
            "name": "Apache License 2.0",
            "description": "A permissive license whose main conditions require preservation of copyright and license notices. Contributors provide an express grant of patent rights.",
            "permissions": ["Commercial use", "Modification", "Distribution", "Patent use", "Private use"],
            "conditions": ["License and copyright notice", "State changes"],
            "limitations": ["Liability", "Warranty", "Trademark use"],
            "template": """                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute,
          must include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   Copyright [year] [fullname]

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License."""
        },
        "unlicense": {
            "name": "The Unlicense",
            "description": "A license with no conditions whatsoever which dedicates works to the public domain. Unlicensed works, modifications, and larger works may be distributed under different terms and without source code.",
            "permissions": ["Commercial use", "Modification", "Distribution", "Private use"],
            "conditions": [],
            "limitations": ["Liability", "Warranty"],
            "template": """This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <https://unlicense.org>"""
        }
    }

    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir

    def list_licenses(self) -> List[str]:
        """Returns a list of available license keys."""
        return sorted(list(self.LICENSES.keys()))

    def get_license_details(self, license_key: str) -> Optional[Dict[str, Any]]:
        """Returns details for a specific license."""
        return self.LICENSES.get(license_key)

    def generate_license_content(self, license_key: str, holder_name: str, year: str = None) -> Optional[str]:
        """Generates the license text with placeholders filled."""
        details = self.get_license_details(license_key)
        if not details:
            return None

        template = details["template"]
        year = year or str(datetime.datetime.now().year)

        # Replace placeholders
        content = template.replace("[year]", str(year))
        content = content.replace("[fullname]", holder_name)

        return content

    def generate_license_file(self, license_key: str, holder_name: str, year: str = None, output_path: Path = None) -> bool:
        """Generates and saves the LICENSE file."""
        content = self.generate_license_content(license_key, holder_name, year)
        if not content:
            return False

        if output_path is None:
            if self.project_dir:
                output_path = self.project_dir / "LICENSE"
            else:
                return False

        try:
            output_path.write_text(content, encoding="utf-8")
            return True
        except IOError as e:
            print(f"Error writing license file: {e}", file=sys.stderr)
            return False

    def check_dependencies(self, allow_list: List[str] = None, deny_list: List[str] = None) -> List[Dict[str, Any]]:
        """Wrapper around DependencyAnalyzer to check licenses."""
        if not self.project_dir:
            return []

        analyzer = DependencyAnalyzer(self.project_dir)
        data = analyzer.scan()
        return analyzer.check_licenses(data, allow_list=allow_list, deny_list=deny_list)


def run_license_lab_logic(args) -> bool:
    """CLI handler for License Lab."""
    project_dir = args.project_dir.resolve()
    manager = LicenseLabManager(project_dir)

    if args.action == "list":
        print("--- Available Licenses ---")
        for key, details in manager.LICENSES.items():
            print(f"{key:<15} : {details['name']}")
        return True

    elif args.action == "explain":
        if not args.type:
            print("Error: --type required for 'explain'.", file=sys.stderr)
            return False

        details = manager.get_license_details(args.type)
        if not details:
            print(f"Error: License '{args.type}' not found.", file=sys.stderr)
            return False

        print(f"--- {details['name']} ---")
        print(f"Description: {details['description']}\n")
        print(f"Permissions: {', '.join(details['permissions'])}")
        print(f"Conditions:  {', '.join(details['conditions'])}")
        print(f"Limitations: {', '.join(details['limitations'])}")
        return True

    elif args.action == "generate":
        if not args.type or not args.holder:
            print("Error: --type and --holder are required for 'generate'.", file=sys.stderr)
            return False

        output_path = Path(args.output).resolve() if args.output else project_dir / "LICENSE"

        if output_path.exists() and not args.force:
            print(f"Error: {output_path.name} already exists. Use --force to overwrite.", file=sys.stderr)
            return False

        if manager.generate_license_file(args.type, args.holder, args.year, output_path):
            print(f"✅ Generated {details['name'] if (details := manager.get_license_details(args.type)) else args.type} at {output_path}")
            return True
        else:
            print("Error generating license file.", file=sys.stderr)
            return False

    elif args.action == "check":
        # Re-use existing logic logic but routed through here
        results = manager.check_dependencies(
            allow_list=args.allow.split(",") if args.allow else None,
            deny_list=args.deny.split(",") if args.deny else None
        )

        print(f"\n--- Dependency License Check ---")
        print(f"  {'Package':<30} | {'License':<20} | {'Status':<10}")
        print("  " + "-" * 70)
        for item in results:
            pkg = item["package"]
            lic = item["license"]
            status = item["status"]

            color = ""
            reset = ""
            if status == "VIOLATION":
                color = "\033[91m" # Red
                reset = "\033[0m"
            elif status == "OK":
                color = "\033[92m" # Green
                reset = "\033[0m"

            print(f"  {pkg:<30} | {lic:<20} | {color}{status:<10}{reset}")
            if item["message"]:
                print(f"    -> {item['message']}")

        return True

    return True
