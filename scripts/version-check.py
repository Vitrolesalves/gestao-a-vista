#!/usr/bin/env python3
"""
Script de verificação de versão para Gestão à Vista
Verifica consistência de versões em diferentes arquivos
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class VersionChecker:
    """Verificador de consistência de versões"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.issues = []
        self.warnings = []

    def add_issue(self, message: str):
        """Adiciona um problema crítico"""
        self.issues.append(f"❌ {message}")

    def add_warning(self, message: str):
        """Adiciona um aviso"""
        self.warnings.append(f"⚠️  {message}")

    def get_version_from_file(self, file_path: Path) -> Optional[str]:
        """Extrai versão de um arquivo"""
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content.strip()
        except Exception as e:
            self.add_warning(f"Could not read {file_path}: {e}")
            return None

    def get_version_from_package_json(self) -> Optional[str]:
        """Extrai versão do package.json"""
        package_json = self.project_root / "package.json"
        if not package_json.exists():
            return None

        try:
            with open(package_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("version")
        except Exception as e:
            self.add_warning(f"Could not parse package.json: {e}")
            return None

    def get_version_from_setup_py(self) -> Optional[str]:
        """Extrai versão do setup.py"""
        setup_py = self.project_root / "setup.py"
        if not setup_py.exists():
            return None

        try:
            with open(setup_py, "r", encoding="utf-8") as f:
                content = f.read()

            # Procurar por version= no setup.py
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
        except Exception as e:
            self.add_warning(f"Could not parse setup.py: {e}")

        return None

    def get_version_from_git_tag(self) -> Optional[str]:
        """Obtém a última tag git"""
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            if result.returncode == 0:
                tag = result.stdout.strip()
                # Remove 'v' prefix se presente
                return tag.lstrip("v")
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return None

    def get_version_from_changelog(self) -> Optional[str]:
        """Extrai a última versão do CHANGELOG.md"""
        changelog = self.project_root / "CHANGELOG.md"
        if not changelog.exists():
            return None

        try:
            with open(changelog, "r", encoding="utf-8") as f:
                content = f.read()

            # Procurar por padrão [vX.Y.Z] no changelog
            matches = re.findall(r"\[v?(\d+\.\d+\.\d+(?:-[^]]+)?)\]", content)
            if matches:
                return matches[0]  # Primeira ocorrência (mais recente)
        except Exception as e:
            self.add_warning(f"Could not parse CHANGELOG.md: {e}")

        return None

    def get_version_from_docker_compose(self) -> Optional[str]:
        """Extrai versão do docker-compose.yml"""
        docker_compose = self.project_root / "docker-compose.yml"
        if not docker_compose.exists():
            return None

        try:
            with open(docker_compose, "r", encoding="utf-8") as f:
                content = f.read()

            # Procurar por image: gestao-a-vista:version
            match = re.search(r"image:\s*[^:]+:([^\s]+)", content)
            if match:
                version = match.group(1)
                if version not in ["latest", "dev", "staging"]:
                    return version
        except Exception as e:
            self.add_warning(f"Could not parse docker-compose.yml: {e}")

        return None

    def check_version_consistency(self) -> Dict[str, Optional[str]]:
        """Verifica consistência entre todas as fontes de versão"""

        versions = {
            "VERSION file": self.get_version_from_file(self.project_root / "VERSION"),
            "package.json": self.get_version_from_package_json(),
            "setup.py": self.get_version_from_setup_py(),
            "git tag": self.get_version_from_git_tag(),
            "CHANGELOG.md": self.get_version_from_changelog(),
            "docker-compose.yml": self.get_version_from_docker_compose(),
        }

        # Filtrar versões None
        valid_versions = {k: v for k, v in versions.items() if v is not None}

        if not valid_versions:
            self.add_issue("No version information found in any file")
            return versions

        # Verificar se todas as versões são iguais
        unique_versions = set(valid_versions.values())

        if len(unique_versions) == 1:
            print(f"✅ All version sources are consistent: {list(unique_versions)[0]}")
        else:
            self.add_issue("Version inconsistency detected:")
            for source, version in valid_versions.items():
                print(f"   {source}: {version}")

        return versions

    def check_semantic_version_format(self, version: str) -> bool:
        """Verifica se a versão segue o formato semântico"""
        if not version:
            return False

        # Regex para SemVer: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
        pattern = (
            r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z\-\.]+))?(?:\+([0-9A-Za-z\-\.]+))?$"
        )

        if re.match(pattern, version):
            return True
        else:
            self.add_issue(
                f"Version '{version}' does not follow semantic versioning format"
            )
            return False

    def check_git_status(self):
        """Verifica status do git"""
        try:
            # Verificar se há mudanças não commitadas
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode == 0:
                uncommitted = result.stdout.strip()
                if uncommitted:
                    self.add_warning("There are uncommitted changes:")
                    for line in uncommitted.split("\n"):
                        print(f"     {line}")
                else:
                    print("✅ Working directory is clean")

            # Verificar se há commits não pushados
            result = subprocess.run(
                ["git", "log", "@{u}..HEAD", "--oneline"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode == 0:
                unpushed = result.stdout.strip()
                if unpushed:
                    self.add_warning("There are unpushed commits:")
                    for line in unpushed.split("\n")[
                        :5
                    ]:  # Mostrar apenas os primeiros 5
                        print(f"     {line}")
                    if len(unpushed.split("\n")) > 5:
                        remaining = len(unpushed.split("\n")) - 5
                        print(f"     ... and {remaining} more")
                else:
                    print("✅ All commits are pushed")

        except (subprocess.SubprocessError, FileNotFoundError):
            self.add_warning("Could not check git status (git not available)")

    def check_changelog_format(self):
        """Verifica formato do CHANGELOG.md"""
        changelog = self.project_root / "CHANGELOG.md"
        if not changelog.exists():
            self.add_warning("CHANGELOG.md not found")
            return

        try:
            with open(changelog, "r", encoding="utf-8") as f:
                content = f.read()

            # Verificar se segue Keep a Changelog format
            if "Keep a Changelog" not in content:
                self.add_warning(
                    "CHANGELOG.md doesn't reference Keep a Changelog format"
                )

            if "Semantic Versioning" not in content:
                self.add_warning("CHANGELOG.md doesn't reference Semantic Versioning")

            # Verificar se há seção Unreleased
            if "[Unreleased]" not in content:
                self.add_warning("CHANGELOG.md doesn't have [Unreleased] section")

            # Contar entradas de versão
            version_entries = re.findall(r"\[v?\d+\.\d+\.\d+[^\]]*\]", content)
            print(f"✅ Found {len(version_entries)} version entries in CHANGELOG.md")

        except Exception as e:
            self.add_warning(f"Could not analyze CHANGELOG.md: {e}")

    def check_docker_files(self):
        """Verifica arquivos Docker"""
        dockerfile = self.project_root / "Dockerfile"
        docker_compose = self.project_root / "docker-compose.yml"

        if dockerfile.exists():
            print("✅ Dockerfile found")
        else:
            self.add_warning("Dockerfile not found")

        if docker_compose.exists():
            print("✅ docker-compose.yml found")
        else:
            self.add_warning("docker-compose.yml not found")

    def check_ci_cd_files(self):
        """Verifica arquivos de CI/CD"""
        github_workflows = self.project_root / ".github" / "workflows"

        if github_workflows.exists():
            workflow_files = list(github_workflows.glob("*.yml")) + list(
                github_workflows.glob("*.yaml")
            )
            if workflow_files:
                print(f"✅ Found {len(workflow_files)} GitHub workflow files")
                for wf in workflow_files:
                    print(f"   - {wf.name}")
            else:
                self.add_warning("No GitHub workflow files found")
        else:
            self.add_warning("No .github/workflows directory found")

    def run_full_check(self) -> bool:
        """Executa verificação completa"""
        print("🔍 Gestão à Vista - Version Consistency Check")
        print("=" * 50)

        # Verificar consistência de versões
        print("\n📋 Checking version consistency...")
        versions = self.check_version_consistency()

        # Verificar formato semântico da versão principal
        main_version = versions.get("VERSION file") or versions.get("git tag")
        if main_version:
            print(f"\n🔢 Checking semantic version format for: {main_version}")
            self.check_semantic_version_format(main_version)

        # Verificar status do git
        print("\n📝 Checking git status...")
        self.check_git_status()

        # Verificar CHANGELOG
        print("\n📚 Checking CHANGELOG format...")
        self.check_changelog_format()

        # Verificar arquivos Docker
        print("\n🐳 Checking Docker files...")
        self.check_docker_files()

        # Verificar CI/CD
        print("\n🚀 Checking CI/CD configuration...")
        self.check_ci_cd_files()

        # Resumo
        print("\n" + "=" * 50)
        print("📊 SUMMARY")
        print("=" * 50)

        if self.issues:
            print(f"\n🚨 ISSUES FOUND ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  {issue}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")

        if not self.issues and not self.warnings:
            print("\n🎉 All checks passed! Project is ready for release.")
            return True
        elif not self.issues:
            print(
                "\n✅ No critical issues found, but there are some warnings to review."
            )
            return True
        else:
            print(
                f"\n❌ Found {len(self.issues)} critical issues that need to be fixed."
            )
            return False


def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Version consistency checker for Gestão à Vista"
    )
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with non-zero code if issues are found",
    )

    args = parser.parse_args()

    checker = VersionChecker(args.project_root)
    success = checker.run_full_check()

    if args.exit_code and not success:
        sys.exit(1)

    return success


if __name__ == "__main__":
    main()
