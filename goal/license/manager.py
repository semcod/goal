"""License manager for handling license templates and file operations."""

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

import click

from goal.user_config import UserConfig


# License templates
LICENSE_TEMPLATES = {
    "MIT": """MIT License

Copyright (c) {year} {fullname}

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
SOFTWARE.
""",
    "Apache-2.0": """                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity granting the License.

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
      (which shall not include communications that are solely written
      by You).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based upon (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and derivative works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control
      systems, and issue tracking systems that are managed by, or on behalf
      of, the Licensor for the purpose of discussing and improving the Work,
      but excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to use, reproduce, modify, merge, publish,
      distribute, sublicense, and/or sell copies of the Work, and to
      permit persons to whom the Work is furnished to do so, subject to
      the following conditions:

      The above copyright notice and this permission notice shall be
      included in all copies or substantial portions of the Work.

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
          that You distribute, all copyright, trademark, patent,
          attribution and other notices from the Source form of the
          Work, excluding those notices that do not pertain to any
          part of the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute
          must include a readable copy of the attribution notices
          contained within such NOTICE file, excluding those notices
          that do not pertain to any part of the Derivative Works,
          in at least one of the following places: within a NOTICE text
          file distributed as part of the Derivative Works; within the
          Source form or documentation, if provided along with the
          Derivative Works; or, within a display generated by the
          Derivative Works, if and wherever such third-party notices
          normally appear. The contents of the NOTICE file are for
          informational purposes only and do not modify the License.
          You may add Your own attribution notices within Derivative
          Works that You distribute, alongside or as an addendum to
          the NOTICE text from the Work, provided that such additional
          attribution notices cannot be construed as modifying the License.

      You may add Your own copyright notice to Your modifications and
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

   9. Accepting Warranty or Support. You may choose to offer, and to
      charge a fee for, warranty, support, indemnity or other liability
      obligations and/or rights consistent with this License. However, in
      accepting such obligations, You may act only on Your own behalf and
      on Your sole responsibility, not on behalf of any other Contributor,
      and only if You agree to indemnify, defend, and hold each Contributor
      harmless for any liability incurred by, or claims asserted against,
      such Contributor by reason of your accepting any such warranty or support.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright {year} {fullname}

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
""",
    "GPL-3.0": """                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) {year} {fullname}

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <https://www.gnu.org/licenses/>.

""",
    "BSD-3-Clause": """BSD 3-Clause License

Copyright (c) {year} {fullname}

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
""",
    "ISC": """ISC License

Copyright (c) {year} {fullname}

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
""",
}


class LicenseManager:
    """Manages license operations including template handling and file creation."""

    def __init__(self, project_dir: Optional[Path] = None):
        """Initialize license manager.

        Args:
            project_dir: Project directory path (defaults to current directory)
        """
        self.project_dir = project_dir or Path.cwd()
        self.custom_templates_dir = self.project_dir / ".goal" / "license-templates"
        self.license_file = self.project_dir / "LICENSE"

    def get_available_licenses(self) -> List[str]:
        """Get list of available license templates."""
        licenses = list(LICENSE_TEMPLATES.keys())

        # Add custom templates
        if self.custom_templates_dir.exists():
            for template_file in self.custom_templates_dir.glob("*.txt"):
                license_id = template_file.stem
                if license_id not in licenses:
                    licenses.append(license_id)

        return sorted(licenses)

    def get_license_template(self, license_id: str) -> Optional[str]:
        """Get license template by ID.

        Args:
            license_id: SPDX license ID

        Returns:
            License template string or None if not found
        """
        # Check built-in templates first
        if license_id in LICENSE_TEMPLATES:
            return LICENSE_TEMPLATES[license_id]

        # Check custom templates
        template_file = self.custom_templates_dir / f"{license_id}.txt"
        if template_file.exists():
            return template_file.read_text(encoding="utf-8")

        return None

    def add_custom_template(self, license_id: str, template: str) -> None:
        """Add a custom license template.

        Args:
            license_id: SPDX license ID or custom identifier
            template: License template text with {year} and {fullname} placeholders
        """
        # Create directory if it doesn't exist
        self.custom_templates_dir.mkdir(parents=True, exist_ok=True)

        # Write template
        template_file = self.custom_templates_dir / f"{license_id}.txt"
        template_file.write_text(template, encoding="utf-8")

        click.echo(click.style(f"✓ Added custom template: {license_id}", fg="green"))

    def create_license_file(
        self,
        license_id: str,
        fullname: Optional[str] = None,
        year: Optional[int] = None,
        force: bool = False,
    ) -> bool:
        """Create a LICENSE file with the specified license.

        Args:
            license_id: SPDX license ID
            fullname: Full name of the copyright holder
            year: Copyright year (defaults to current year)
            force: Overwrite existing LICENSE file

        Returns:
            True if file was created successfully
        """
        # Validate license ID
        is_valid, msg = validate_spdx_id(license_id)
        if not is_valid and license_id not in self.get_available_licenses():
            click.echo(click.style(f"✗ Invalid license ID: {msg}", fg="red"))
            return False

        # Check if file exists
        if self.license_file.exists() and not force:
            click.echo(click.style("⚠ LICENSE file already exists", fg="yellow"))
            if not click.confirm(click.style("Overwrite?", fg="cyan"), default=False):
                return False

        # Get template
        template = self.get_license_template(license_id)
        if not template:
            click.echo(
                click.style(f"✗ No template found for license: {license_id}", fg="red")
            )
            return False

        # Get user info if not provided
        if not fullname:
            user_config = UserConfig()
            fullname = user_config.get("author_name", "Author Name")

        if not year:
            year = datetime.now().year

        # Fill template
        content = template.format(year=year, fullname=fullname)

        # Write file
        try:
            self.license_file.write_text(content, encoding="utf-8")
            click.echo(
                click.style(f"✓ Created LICENSE file with {license_id}", fg="green")
            )
            return True
        except Exception as e:
            click.echo(click.style(f"✗ Failed to create LICENSE file: {e}", fg="red"))
            return False

    def update_license_file(
        self,
        license_id: Optional[str] = None,
        fullname: Optional[str] = None,
        year: Optional[int] = None,
    ) -> bool:
        """Update existing LICENSE file.

        Args:
            license_id: New SPDX license ID (if None, keeps current)
            fullname: New full name (if None, keeps current)
            year: New year (if None, keeps current)

        Returns:
            True if file was updated successfully
        """
        if not self.license_file.exists():
            click.echo(click.style("✗ No LICENSE file found", fg="red"))
            return False

        # If no changes requested, just validate
        if not any([license_id, fullname, year]):
            click.echo(click.style("ℹ No updates specified", fg="cyan"))
            return True

        current_content = self.license_file.read_text(encoding="utf-8")

        license_id = self._resolve_license_id(current_content, license_id)
        if not license_id:
            return False

        if not fullname:
            extracted_year, extracted_fullname = self._extract_owner_from_content(
                current_content
            )
            if extracted_fullname:
                year = extracted_year
                fullname = extracted_fullname
            else:
                user_config = UserConfig()
                fullname = user_config.get("author_name", "Author Name")

        if not year:
            year = datetime.now().year

        # Create new content
        return self.create_license_file(license_id, fullname, year, force=True)

    # Ordered (license_id, required_substrings) for detection; first match wins.
    _LICENSE_SIGNATURES = [
        ("MIT", ["Permission is hereby granted"]),
        ("Apache-2.0", ["Apache License", "Version 2.0"]),
        ("GPL-3.0", ["GNU GENERAL PUBLIC LICENSE"]),
        ("BSD-3-Clause", ["BSD 3-Clause License"]),
        ("ISC", ["ISC License"]),
    ]

    @classmethod
    def _detect_license_type(cls, content: str) -> Optional[str]:
        """Return the SPDX license ID detected in *content*, or None."""
        for lid, signatures in cls._LICENSE_SIGNATURES:
            if all(sig in content for sig in signatures):
                return lid
        return None

    def _resolve_license_id(
        self, current_content: str, license_id: Optional[str]
    ) -> Optional[str]:
        if license_id:
            return license_id

        license_id = self._detect_license_type(current_content)
        if license_id:
            return license_id

        click.echo(click.style("⚠ Could not detect current license type", fg="yellow"))
        if not click.confirm(click.style("Proceed anyway?", fg="cyan"), default=False):
            return None
        return license_id

    @staticmethod
    def _extract_owner_from_content(
        content: str,
    ) -> tuple[Optional[int], Optional[str]]:
        match = re.search(r"Copyright(?: \(c\))? (\d+) (.+)", content)
        if match:
            return int(match.group(1)), match.group(2)
        return None, None

    def validate_license_file(self) -> Tuple[bool, List[str]]:
        """Validate the LICENSE file.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        if not self.license_file.exists():
            return False, ["LICENSE file does not exist"]

        issues: List[str] = []
        content = self.license_file.read_text(encoding="utf-8")

        if not content.strip():
            return False, ["LICENSE file is empty"]

        detected = self._detect_license_type(content)
        if not detected:
            issues.append("Could not detect license type")
        else:
            is_valid, msg = validate_spdx_id(detected)
            if not is_valid:
                issues.append(f"Invalid SPDX license: {msg}")

        if "{year}" in content or "{fullname}" in content:
            issues.append("License contains unfilled placeholders")

        if not re.search(r"copyright", content, re.IGNORECASE):
            issues.append("No copyright notice found")

        return len(issues) == 0, issues


def create_license_file(
    license_id: str,
    fullname: Optional[str] = None,
    year: Optional[int] = None,
    force: bool = False,
) -> bool:
    """Convenience function to create a LICENSE file.

    Args:
        license_id: SPDX license ID
        fullname: Full name of the copyright holder
        year: Copyright year (defaults to current year)
        force: Overwrite existing LICENSE file

    Returns:
        True if file was created successfully
    """
    manager = LicenseManager()
    return manager.create_license_file(license_id, fullname, year, force)


def update_license_file(
    license_id: Optional[str] = None,
    fullname: Optional[str] = None,
    year: Optional[int] = None,
) -> bool:
    """Convenience function to update a LICENSE file.

    Args:
        license_id: New SPDX license ID (if None, keeps current)
        fullname: New full name (if None, keeps current)
        year: New year (if None, keeps current)

    Returns:
        True if file was updated successfully
    """
    manager = LicenseManager()
    return manager.update_license_file(license_id, fullname, year)
