#!/usr/bin/env python3
"""
Pre-deployment validation script for products initialized from this template.

Checks that all prerequisites are met before deploying to cloud infrastructure.
Run with: python scripts/pre_deploy_check.py [--env staging|production]

Exit codes:
    0 - All checks passed
    1 - One or more checks failed
    2 - Configuration error
"""

import argparse
import base64
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class Colors:
    """Terminal colors for output."""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


# ASCII-safe status indicators for Windows compatibility
PASS_MARK = "[PASS]"
FAIL_MARK = "[FAIL]"


class CheckResult:
    """Result of a single validation check."""
    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message


class PreDeployChecker:
    """Runs pre-deployment validation checks."""
    
    def __init__(self, environment: str = "staging"):
        self.environment = environment
        self.results: List[CheckResult] = []
        self.errors: List[str] = []
        
    def run_all_checks(self) -> bool:
        """Run all validation checks. Returns True if all passed."""
        print(f"{Colors.BLUE}Running pre-deployment checks for environment: {self.environment}{Colors.RESET}\n")
        
        # Security checks
        self._check_no_secrets_in_git()
        self._check_env_files_not_committed()
        
        # Configuration checks
        self._check_required_files_exist()
        self._check_kustomize_overlays()
        self._check_domain_configured()
        
        # Infrastructure checks
        self._check_kubernetes_connection()
        self._check_namespace_exists()
        self._check_secrets_exist()
        
        # Database checks
        self._check_database_env_vars()
        
        # Print summary
        return self._print_summary()
    
    def _check_no_secrets_in_git(self) -> None:
        """Check that no secrets are committed to Git."""
        secret_patterns = [
            r'SECRET_KEY\s*=\s*["\']?changethis',
            r'POSTGRES_PASSWORD\s*=\s*["\']?changethis',
            r'FIRST_SUPERUSER_PASSWORD\s*=\s*["\']?changethis',
            r'password\s*=\s*["\']?password',
            r'apikey\s*=\s*["\']?SG\.',  # SendGrid pattern
        ]
        
        try:
            # Check common secret locations
            files_to_check = [
                ".env",
                ".env.example",
                ".env.staging",
                ".env.production",
            ]
            
            found_secrets = []
            for file in files_to_check:
                if Path(file).exists():
                    content = Path(file).read_text()
                    for pattern in secret_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            found_secrets.append(f"{file}: {pattern}")
            
            if found_secrets:
                self.results.append(CheckResult(
                    "No secrets in Git",
                    False,
                    f"Found default/changed passwords in: {', '.join(found_secrets)}"
                ))
            else:
                self.results.append(CheckResult("No secrets in Git", True))
                
        except Exception as e:
            self.results.append(CheckResult("No secrets in Git", False, str(e)))
    
    def _check_env_files_not_committed(self) -> None:
        """Check that .env files are in .gitignore."""
        try:
            gitignore = Path(".gitignore")
            if not gitignore.exists():
                self.results.append(CheckResult(
                    ".env files in .gitignore",
                    False,
                    ".gitignore does not exist"
                ))
                return
            
            content = gitignore.read_text()
            required_patterns = [".env", ".env.*"]
            missing = [p for p in required_patterns if p not in content]
            
            if missing:
                self.results.append(CheckResult(
                    ".env files in .gitignore",
                    False,
                    f"Missing patterns: {', '.join(missing)}"
                ))
            else:
                self.results.append(CheckResult(".env files in .gitignore", True))
                
        except Exception as e:
            self.results.append(CheckResult(".env files in .gitignore", False, str(e)))
    
    def _check_required_files_exist(self) -> None:
        """Check that required configuration files exist."""
        required_files = [
            f"deploy/k8s/overlays/{self.environment}/kustomization.yaml",
            "deploy/k8s/base/deployment.yaml",
            "deploy/k8s/base/service.yaml",
            ".env.example",
        ]
        
        missing = [f for f in required_files if not Path(f).exists()]
        
        if missing:
            self.results.append(CheckResult(
                "Required files exist",
                False,
                f"Missing files: {', '.join(missing)}"
            ))
        else:
            self.results.append(CheckResult("Required files exist", True))
    
    def _check_kustomize_overlays(self) -> None:
        """Check that Kustomize overlays are valid."""
        overlay_path = f"deploy/k8s/overlays/{self.environment}"
        
        if not Path(overlay_path).exists():
            self.results.append(CheckResult(
                "Kustomize overlays valid",
                False,
                f"Overlay directory does not exist: {overlay_path}"
            ))
            return
        
        try:
            # Try to build the overlay
            result = subprocess.run(
                ["kustomize", "build", overlay_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.results.append(CheckResult("Kustomize overlays valid", True))
            else:
                self.results.append(CheckResult(
                    "Kustomize overlays valid",
                    False,
                    f"kustomize build failed: {result.stderr}"
                ))
        except FileNotFoundError:
            # kustomize not installed, skip this check
            self.results.append(CheckResult(
                "Kustomize overlays valid",
                True,
                "kustomize not installed, skipping validation"
            ))
        except Exception as e:
            self.results.append(CheckResult("Kustomize overlays valid", False, str(e)))
    
    def _check_domain_configured(self) -> None:
        """Check that domain is configured (not localhost)."""
        env_file = f".env.{self.environment}"
        
        if not Path(env_file).exists():
            self.results.append(CheckResult(
                "Domain configured",
                False,
                f"Environment file not found: {env_file}"
            ))
            return
        
        try:
            content = Path(env_file).read_text()
            
            # Check DOMAIN
            domain_match = re.search(r'DOMAIN\s*=\s*(.+)', content)
            if not domain_match:
                self.results.append(CheckResult(
                    "Domain configured",
                    False,
                    "DOMAIN not set in environment file"
                ))
                return
            
            domain = domain_match.group(1).strip().strip('"\'')
            
            if domain in ["localhost", "127.0.0.1", ""]:
                self.results.append(CheckResult(
                    "Domain configured",
                    False,
                    f"DOMAIN is set to {domain}, must be a real domain"
                ))
            else:
                self.results.append(CheckResult("Domain configured", True, f"Domain: {domain}"))
                
        except Exception as e:
            self.results.append(CheckResult("Domain configured", False, str(e)))
    
    def _check_kubernetes_connection(self) -> None:
        """Check that kubectl can connect to cluster."""
        try:
            result = subprocess.run(
                ["kubectl", "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.results.append(CheckResult("Kubernetes connection", True))
            else:
                self.results.append(CheckResult(
                    "Kubernetes connection",
                    False,
                    "kubectl cannot connect to cluster"
                ))
        except FileNotFoundError:
            self.results.append(CheckResult(
                "Kubernetes connection",
                False,
                "kubectl not found in PATH"
            ))
        except Exception as e:
            self.results.append(CheckResult("Kubernetes connection", False, str(e)))
    
    def _check_namespace_exists(self) -> None:
        """Check that namespace exists in cluster."""
        namespace = "prod" if self.environment == "production" else self.environment
        
        try:
            result = subprocess.run(
                ["kubectl", "get", "namespace", namespace],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.results.append(CheckResult(f"Namespace '{namespace}' exists", True))
            else:
                self.results.append(CheckResult(
                    f"Namespace '{namespace}' exists",
                    False,
                    f"Namespace {namespace} not found. Create with: kubectl create namespace {namespace}"
                ))
        except Exception as e:
            self.results.append(CheckResult(f"Namespace '{namespace}' exists", False, str(e)))
    
    def _check_secrets_exist(self) -> None:
        """Check that Kubernetes secrets exist."""
        namespace = "prod" if self.environment == "production" else self.environment
        
        try:
            result = subprocess.run(
                ["kubectl", "get", "secret", "api-secrets", "-n", namespace],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.results.append(CheckResult("Kubernetes secrets exist", True))
            else:
                self.results.append(CheckResult(
                    "Kubernetes secrets exist",
                    False,
                    f"Secret 'api-secrets' not found in namespace {namespace}. "
                    f"Create with: kubectl create secret generic api-secrets -n {namespace} ..."
                ))
        except Exception as e:
            self.results.append(CheckResult("Kubernetes secrets exist", False, str(e)))
    
    def _check_database_env_vars(self) -> None:
        """Check that database environment variables are set."""
        env_file = f".env.{self.environment}"
        
        if not Path(env_file).exists():
            self.results.append(CheckResult(
                "Database configuration",
                False,
                f"Environment file not found: {env_file}"
            ))
            return
        
        try:
            content = Path(env_file).read_text()
            
            required_vars = [
                "POSTGRES_SERVER",
                "POSTGRES_PORT",
                "POSTGRES_DB",
                "POSTGRES_USER",
            ]
            
            missing = []
            for var in required_vars:
                if not re.search(rf'{var}\s*=', content):
                    missing.append(var)
            
            if missing:
                self.results.append(CheckResult(
                    "Database configuration",
                    False,
                    f"Missing database env vars: {', '.join(missing)}"
                ))
            else:
                # Check if using placeholder values
                if "localhost" in content and self.environment != "local":
                    self.results.append(CheckResult(
                        "Database configuration",
                        False,
                        "Database is set to localhost, should be managed DB host"
                    ))
                else:
                    self.results.append(CheckResult("Database configuration", True))
                    
        except Exception as e:
            self.results.append(CheckResult("Database configuration", False, str(e)))
    
    def _print_summary(self) -> bool:
        """Print summary of all checks. Returns True if all passed."""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BLUE}CHECK SUMMARY{Colors.RESET}")
        print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
        
        passed = 0
        failed = 0
        
        for result in self.results:
            if result.passed:
                status = f"{Colors.GREEN}{PASS_MARK}{Colors.RESET}"
                passed += 1
            else:
                status = f"{Colors.RED}{FAIL_MARK}{Colors.RESET}"
                failed += 1
            
            print(f"{status} {result.name}")
            if result.message:
                print(f"       {Colors.YELLOW}{result.message}{Colors.RESET}")
        
        print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"Total: {passed + failed} | {Colors.GREEN}Passed: {passed}{Colors.RESET} | {Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
        
        if failed > 0:
            print(f"{Colors.RED}Pre-deployment checks failed. Fix issues above before deploying.{Colors.RESET}\n")
            return False
        else:
            print(f"{Colors.GREEN}All checks passed! Ready for deployment.{Colors.RESET}\n")
            return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Pre-deployment validation for cloud deployments"
    )
    parser.add_argument(
        "--env",
        choices=["staging", "production", "dev"],
        default="staging",
        help="Target environment (default: staging)"
    )
    
    args = parser.parse_args()
    
    checker = PreDeployChecker(environment=args.env)
    success = checker.run_all_checks()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
