#!/usr/bin/env python3
"""
Quality Gate: Documentation Link Validation
Validates all internal links in the docs/ directory and ensures no broken references exist.
This quality gate is dynamic and works regardless of how the docs/ directory changes.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Set

def find_markdown_files(docs_dir: str = "docs/") -> List[str]:
    """Find all markdown files in the docs directory."""
    markdown_files = []
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md'):
                markdown_files.append(os.path.join(root, file))
    return markdown_files

def extract_internal_links(markdown_files: List[str]) -> List[Tuple[str, str, str]]:
    """
    Extract all internal links from markdown files.
    Returns list of (file_path, link_text, link_url) tuples.
    """
    internal_links = []
    link_pattern = r'\[([^\]]*)\]\(([^)]*)\)'
    
    for file_path in markdown_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = re.findall(link_pattern, content)
                for link_text, link_url in matches:
                    # Skip external links
                    if not link_url.startswith('http') and not link_url.startswith('#'):
                        internal_links.append((file_path, link_text, link_url))
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
    
    return internal_links

def validate_link_exists(link_url: str, base_dir: str = ".") -> bool:
    """
    Check if a link points to an existing file.
    Tries multiple possible paths and extensions.
    """
    possible_paths = [
        link_url,
        f"{link_url}.md",
        f"docs/{link_url}",
        f"docs/{link_url}.md",
        os.path.join(base_dir, link_url),
        os.path.join(base_dir, f"{link_url}.md"),
        os.path.join(base_dir, "docs", link_url),
        os.path.join(base_dir, "docs", f"{link_url}.md")
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.path.isfile(path):
            return True
    
    return False

def validate_section_references(markdown_files: List[str]) -> List[Tuple[str, str]]:
    """
    Validate section references (links starting with #).
    Returns list of (file_path, section_ref) tuples for invalid references.
    """
    invalid_sections = []
    section_pattern = r'\[([^\]]*)\]\(#([^)]*)\)'
    
    for file_path in markdown_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = re.findall(section_pattern, content)
                for link_text, section_ref in matches:
                    # Check if section exists in the same file
                    section_heading = f"# {section_ref.replace('-', ' ').title()}"
                    if section_heading not in content and f"## {section_ref}" not in content:
                        invalid_sections.append((file_path, section_ref))
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
    
    return invalid_sections

def run_quality_gate() -> Dict:
    """Run the documentation link validation quality gate."""
    print("=== Documentation Link Validation Quality Gate ===")
    print(f"Timestamp: {subprocess.check_output(['date']).decode().strip()}")
    print()
    
    # Find all markdown files
    print("1. Scanning markdown files in docs/:")
    markdown_files = find_markdown_files()
    total_files = len(markdown_files)
    print(f"Found {total_files} markdown files")
    print()
    
    # Extract internal links
    print("2. Extracting all internal links:")
    internal_links = extract_internal_links(markdown_files)
    total_links = len(internal_links)
    print(f"Found {total_links} internal links")
    print()
    
    # Validate links
    print("3. Validating link integrity:")
    broken_links = []
    broken_files = set()
    
    for file_path, link_text, link_url in internal_links:
        if not validate_link_exists(link_url):
            broken_links.append((file_path, link_text, link_url))
            broken_files.add(file_path)
    
    broken_links_count = len(broken_links)
    broken_files_count = len(broken_files)
    
    print("Link validation complete")
    print()
    
    # Validate section references
    print("4. Validating section references:")
    invalid_sections = validate_section_references(markdown_files)
    total_sections = len(invalid_sections)
    print(f"Found {total_sections} invalid section references")
    print()
    
    # Check cross-references
    print("5. Validating cross-references:")
    cross_refs = []
    for file_path in markdown_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'docs/' in content:
                    cross_refs.append(file_path)
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
    
    total_cross_refs = len(cross_refs)
    print(f"Found {total_cross_refs} files with cross-references")
    print()
    
    # Calculate pass rate
    if total_links == 0:
        pass_rate = 100
    else:
        pass_rate = ((total_links - broken_links_count) * 100) // total_links
    
    # Quality Gate Results
    print("=== Quality Gate Results ===")
    print(f"Total markdown files: {total_files}")
    print(f"Total internal links: {total_links}")
    print(f"Broken links: {broken_links_count}")
    print(f"Files with broken links: {broken_files_count}")
    print(f"Invalid section references: {total_sections}")
    print(f"Files with cross-references: {total_cross_refs}")
    print()
    print(f"Link integrity pass rate: {pass_rate}%")
    print()
    
    # Quality Gate Decision
    if broken_links_count == 0 and total_sections == 0:
        print("✅ QUALITY GATE PASSED: All links are valid")
        print(f"All {total_links} internal links are working correctly")
        return {
            "status": "PASSED",
            "total_files": total_files,
            "total_links": total_links,
            "broken_links": broken_links_count,
            "broken_files": broken_files_count,
            "invalid_sections": total_sections,
            "pass_rate": pass_rate,
            "broken_links_list": broken_links,
            "broken_files_list": list(broken_files)
        }
    else:
        print("❌ QUALITY GATE FAILED: Broken links or invalid sections found")
        print()
        
        if broken_links_count > 0:
            print("Broken links:")
            for file_path, link_text, link_url in broken_links:
                print(f"  {file_path}: [{link_text}]({link_url})")
            print()
        
        if total_sections > 0:
            print("Invalid section references:")
            for file_path, section_ref in invalid_sections:
                print(f"  {file_path}: #{section_ref}")
            print()
        
        print("Files with broken links:")
        for file_path in sorted(broken_files):
            print(f"  {file_path}")
        print()
        
        print("Required action: Fix all broken links before proceeding")
        print("Target: 100% link integrity (0 broken links)")
        print(f"Current: {pass_rate}% link integrity ({broken_links_count} broken links)")
        
        return {
            "status": "FAILED",
            "total_files": total_files,
            "total_links": total_links,
            "broken_links": broken_links_count,
            "broken_files": broken_files_count,
            "invalid_sections": total_sections,
            "pass_rate": pass_rate,
            "broken_links_list": broken_links,
            "broken_files_list": list(broken_files)
        }

if __name__ == "__main__":
    try:
        result = run_quality_gate()
        if result["status"] == "FAILED":
            sys.exit(1)
        else:
            sys.exit(0)
    except Exception as e:
        print(f"Error running quality gate: {e}")
        sys.exit(1)
