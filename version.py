#!/usr/bin/env python3
"""
Sistema de Versionamento Semântico para Gestão à Vista
Implementa versionamento automático seguindo SemVer (Semantic Versioning)
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class SemanticVersion:
    """Classe para manipular versões semânticas"""

    def __init__(self, version_string: str = "0.1.0"):
        self.parse(version_string)

    def parse(self, version_string: str):
        """Parse uma string de versão no formato SemVer"""
        # Remove 'v' prefix se presente
        version_string = version_string.lstrip("v")

        # Regex para SemVer: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
        pattern = (
            r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z\-\.]+))?(?:\+([0-9A-Za-z\-\.]+))?$"
        )
        match = re.match(pattern, version_string)

        if not match:
            raise ValueError(f"Invalid semantic version: {version_string}")

        self.major = int(match.group(1))
        self.minor = int(match.group(2))
        self.patch = int(match.group(3))
        self.prerelease = match.group(4) or None
        self.build = match.group(5) or None

    def bump_major(self):
        """Incrementa versão major (breaking changes)"""
        self.major += 1
        self.minor = 0
        self.patch = 0
        self.prerelease = None
        self.build = None

    def bump_minor(self):
        """Incrementa versão minor (new features)"""
        self.minor += 1
        self.patch = 0
        self.prerelease = None
        self.build = None

    def bump_patch(self):
        """Incrementa versão patch (bug fixes)"""
        self.patch += 1
        self.prerelease = None
        self.build = None

    def set_prerelease(self, prerelease: str):
        """Define prerelease (alpha, beta, rc.1, etc.)"""
        self.prerelease = prerelease

    def set_build(self, build: str):
        """Define build metadata"""
        self.build = build

    def __str__(self):
        """Retorna string da versão"""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version

    def __repr__(self):
        return f"SemanticVersion('{str(self)}')"

    def to_tag(self):
        """Retorna versão com prefixo 'v' para tags"""
        return f"v{str(self)}"


class VersionManager:
    """Gerenciador de versionamento do projeto"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.version_file = self.project_root / "VERSION"
        self.changelog_file = self.project_root / "CHANGELOG.md"
        self.package_json = self.project_root / "package.json"
        self.setup_py = self.project_root / "setup.py"

        # Carregar versão atual
        self.current_version = self.load_current_version()

    def load_current_version(self) -> SemanticVersion:
        """Carrega a versão atual do arquivo VERSION ou git tags"""

        # Tentar carregar do arquivo VERSION
        if self.version_file.exists():
            with open(self.version_file, "r") as f:
                version_str = f.read().strip()
                return SemanticVersion(version_str)

        # Tentar carregar da última tag git
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            if result.returncode == 0:
                tag = result.stdout.strip()
                return SemanticVersion(tag)
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # Versão padrão se não encontrar nenhuma
        return SemanticVersion("0.1.0")

    def save_version(self, version: SemanticVersion):
        """Salva a versão nos arquivos do projeto"""

        # Salvar no arquivo VERSION
        with open(self.version_file, "w") as f:
            f.write(str(version))

        # Atualizar package.json se existir
        if self.package_json.exists():
            with open(self.package_json, "r") as f:
                package_data = json.load(f)
            package_data["version"] = str(version)
            with open(self.package_json, "w") as f:
                json.dump(package_data, f, indent=2)

        # Atualizar setup.py se existir
        if self.setup_py.exists():
            with open(self.setup_py, "r") as f:
                content = f.read()

            # Substituir version= no setup.py
            pattern = r'version\s*=\s*["\'][^"\']*["\']'
            replacement = f'version="{str(version)}"'
            content = re.sub(pattern, replacement, content)

            with open(self.setup_py, "w") as f:
                f.write(content)

        self.current_version = version

    def get_git_commits_since_last_tag(self) -> List[str]:
        """Obtém commits desde a última tag"""
        try:
            # Obter última tag
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode == 0:
                last_tag = result.stdout.strip()
                # Obter commits desde a última tag
                result = subprocess.run(
                    ["git", "log", f"{last_tag}..HEAD", "--oneline"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                )
            else:
                # Se não há tags, obter todos os commits
                result = subprocess.run(
                    ["git", "log", "--oneline"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                )

            if result.returncode == 0:
                commits = result.stdout.strip().split("\n")
                return [commit for commit in commits if commit.strip()]

        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return []

    def analyze_commits_for_version_bump(self, commits: List[str]) -> str:
        """Analisa commits para determinar tipo de bump necessário"""

        # Padrões para identificar tipos de mudanças
        breaking_patterns = [
            r"\bBREAKING\s+CHANGE\b",
            r"\bbreaking\s+change\b",
            r"\bBREAKING\b",
            r"!:",  # Conventional Commits breaking change
        ]

        feature_patterns = [
            r"^feat(\(.+\))?:",
            r"^feature(\(.+\))?:",
            r"\bfeat\b",
            r"\bfeature\b",
            r"\bnew\b",
        ]

        fix_patterns = [
            r"^fix(\(.+\))?:",
            r"^bugfix(\(.+\))?:",
            r"\bfix\b",
            r"\bbugfix\b",
            r"\bpatch\b",
        ]

        has_breaking = False
        has_features = False
        has_fixes = False

        for commit in commits:
            commit_lower = commit.lower()

            # Verificar breaking changes
            for pattern in breaking_patterns:
                if re.search(pattern, commit, re.IGNORECASE):
                    has_breaking = True
                    break

            # Verificar features
            for pattern in feature_patterns:
                if re.search(pattern, commit, re.IGNORECASE):
                    has_features = True
                    break

            # Verificar fixes
            for pattern in fix_patterns:
                if re.search(pattern, commit, re.IGNORECASE):
                    has_fixes = True
                    break

        # Determinar tipo de bump
        if has_breaking:
            return "major"
        elif has_features:
            return "minor"
        elif has_fixes:
            return "patch"
        else:
            return "patch"  # Default para mudanças menores

    def update_changelog(self, new_version: SemanticVersion, commits: List[str]):
        """Atualiza o CHANGELOG.md com a nova versão"""

        # Criar CHANGELOG.md se não existir
        if not self.changelog_file.exists():
            with open(self.changelog_file, "w") as f:
                f.write("# Changelog\n\n")
                f.write(
                    "All notable changes to this project will be documented in this file.\n\n"
                )
                f.write(
                    "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\n"
                )
                f.write(
                    "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"
                )

        # Ler conteúdo atual
        with open(self.changelog_file, "r") as f:
            content = f.read()

        # Preparar nova entrada
        date_str = datetime.now().strftime("%Y-%m-%d")
        new_entry = f"## [{new_version.to_tag()}] - {date_str}\n\n"

        # Categorizar commits
        features = []
        fixes = []
        breaking = []
        others = []

        for commit in commits:
            commit_clean = commit.strip()
            if not commit_clean:
                continue

            commit_lower = commit_clean.lower()

            if re.search(
                r"\bBREAKING\s+CHANGE\b|\bbreaking\s+change\b",
                commit_clean,
                re.IGNORECASE,
            ):
                breaking.append(commit_clean)
            elif re.search(
                r"^feat(\(.+\))?:|^feature(\(.+\))?:|\bfeat\b|\bfeature\b",
                commit_clean,
                re.IGNORECASE,
            ):
                features.append(commit_clean)
            elif re.search(
                r"^fix(\(.+\))?:|^bugfix(\(.+\))?:|\bfix\b|\bbugfix\b",
                commit_clean,
                re.IGNORECASE,
            ):
                fixes.append(commit_clean)
            else:
                others.append(commit_clean)

        # Adicionar seções ao changelog
        if breaking:
            new_entry += "### 💥 Breaking Changes\n"
            for item in breaking:
                new_entry += f"- {item}\n"
            new_entry += "\n"

        if features:
            new_entry += "### ✨ Features\n"
            for item in features:
                new_entry += f"- {item}\n"
            new_entry += "\n"

        if fixes:
            new_entry += "### 🐛 Bug Fixes\n"
            for item in fixes:
                new_entry += f"- {item}\n"
            new_entry += "\n"

        if others:
            new_entry += "### 🔧 Other Changes\n"
            for item in others:
                new_entry += f"- {item}\n"
            new_entry += "\n"

        # Inserir nova entrada após o cabeçalho
        lines = content.split("\n")
        header_end = 0
        for i, line in enumerate(lines):
            if line.startswith("## ") and "[" in line:
                header_end = i
                break
            elif i > 10:  # Assumir que cabeçalho não passa de 10 linhas
                header_end = i
                break

        if header_end == 0:
            # Adicionar após cabeçalho padrão
            for i, line in enumerate(lines):
                if line.strip() == "" and i > 5:
                    header_end = i + 1
                    break

        # Inserir nova entrada
        lines.insert(header_end, new_entry.rstrip())

        # Salvar changelog atualizado
        with open(self.changelog_file, "w") as f:
            f.write("\n".join(lines))

    def create_git_tag(self, version: SemanticVersion, message: str = None):
        """Cria tag git para a versão"""
        try:
            tag_name = version.to_tag()
            tag_message = message or f"Release {tag_name}"

            # Criar tag anotada
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", tag_message],
                check=True,
                cwd=self.project_root,
            )

            print(f"✅ Git tag {tag_name} created successfully")
            return True

        except subprocess.SubprocessError as e:
            print(f"❌ Failed to create git tag: {e}")
            return False

    def bump_version(
        self, bump_type: str = "auto", prerelease: str = None, build: str = None
    ) -> SemanticVersion:
        """Incrementa a versão baseado no tipo especificado"""

        new_version = SemanticVersion(str(self.current_version))

        if bump_type == "auto":
            # Analisar commits para determinar bump automático
            commits = self.get_git_commits_since_last_tag()
            if commits:
                bump_type = self.analyze_commits_for_version_bump(commits)
            else:
                bump_type = "patch"

        # Aplicar bump
        if bump_type == "major":
            new_version.bump_major()
        elif bump_type == "minor":
            new_version.bump_minor()
        elif bump_type == "patch":
            new_version.bump_patch()
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")

        # Aplicar prerelease e build se especificados
        if prerelease:
            new_version.set_prerelease(prerelease)
        if build:
            new_version.set_build(build)

        return new_version

    def release(
        self,
        bump_type: str = "auto",
        prerelease: str = None,
        build: str = None,
        create_tag: bool = True,
        update_changelog: bool = True,
    ) -> SemanticVersion:
        """Executa um release completo"""

        print(f"🚀 Starting release process...")
        print(f"Current version: {self.current_version}")

        # Obter commits desde última versão
        commits = self.get_git_commits_since_last_tag()
        print(f"Found {len(commits)} commits since last release")

        # Calcular nova versão
        new_version = self.bump_version(bump_type, prerelease, build)
        print(f"New version: {new_version}")

        # Atualizar arquivos de versão
        self.save_version(new_version)
        print(f"✅ Version files updated")

        # Atualizar changelog
        if update_changelog and commits:
            self.update_changelog(new_version, commits)
            print(f"✅ Changelog updated")

        # Criar tag git
        if create_tag:
            self.create_git_tag(new_version)

        print(f"🎉 Release {new_version.to_tag()} completed successfully!")
        return new_version


def main():
    """Função principal para uso via linha de comando"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Semantic Version Manager for Gestão à Vista"
    )
    parser.add_argument("--current", action="store_true", help="Show current version")
    parser.add_argument(
        "--bump", choices=["major", "minor", "patch", "auto"], help="Bump version type"
    )
    parser.add_argument(
        "--prerelease", help="Set prerelease identifier (alpha, beta, rc.1, etc.)"
    )
    parser.add_argument("--build", help="Set build metadata")
    parser.add_argument("--no-tag", action="store_true", help="Do not create git tag")
    parser.add_argument(
        "--no-changelog", action="store_true", help="Do not update changelog"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    # Inicializar gerenciador
    vm = VersionManager()

    if args.current:
        print(f"Current version: {vm.current_version}")
        return

    if args.bump:
        if args.dry_run:
            new_version = vm.bump_version(args.bump, args.prerelease, args.build)
            print(f"Would bump version from {vm.current_version} to {new_version}")

            commits = vm.get_git_commits_since_last_tag()
            if commits:
                print(f"Commits since last release ({len(commits)}):")
                for commit in commits[:10]:  # Mostrar apenas os primeiros 10
                    print(f"  - {commit}")
                if len(commits) > 10:
                    print(f"  ... and {len(commits) - 10} more")
        else:
            new_version = vm.release(
                bump_type=args.bump,
                prerelease=args.prerelease,
                build=args.build,
                create_tag=not args.no_tag,
                update_changelog=not args.no_changelog,
            )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
