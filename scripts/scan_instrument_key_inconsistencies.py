#!/usr/bin/env python3
"""
Scan entire codebase for instrument/position key format inconsistencies.

Canonical format: venue:position_type:symbol
- venue: binance, aave_v3, wallet, etherfi, lido, etc.
- position_type: BaseToken, aToken, debtToken, Perp
- symbol: USDT, BTC, ETH, BTCUSDT, etc.

This script identifies:
1. Deprecated variable names (instrument_id, instrument_key, position_id)
2. Deprecated format patterns (dot notation like "wallet.USDT")
3. Missing position_type in keys
4. Inconsistent documentation references
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Set
import json

# Canonical format pattern
CANONICAL_PATTERN = r'([a-z_]+):(BaseToken|aToken|debtToken|Perp|Spot):([A-Z][A-Za-z0-9]*)'

# Deprecated patterns to find
DEPRECATED_VARIABLE_NAMES = [
    'instrument_id',
    'instrument_key', 
    'position_id',
    'asset_id',
    'asset_key'
]

# Deprecated format patterns
DEPRECATED_FORMATS = [
    # Dot notation: wallet.USDT, binance.BTC
    r'\b(wallet|binance|bybit|okx|aave|aave_v3|etherfi|lido|morpho)\.(USDT|BTC|ETH|WETH|[a-z][A-Z]\w+)',
    
    # Two-part colon format (missing position_type): binance:USDT, wallet:ETH
    r'\b(wallet|binance|bybit|okx|aave|aave_v3|etherfi|lido|morpho):(USDT|BTC|ETH|WETH|BTCUSDT|ETHUSDT)\b',
    
    # Underscore format: binance_BTC_USDT
    r'\b(wallet|binance|bybit|okx|aave|aave_v3)_([A-Z]{3,})_([A-Z]{3,})',
]


def scan_file(filepath: Path) -> Dict:
    """Scan a single file for inconsistencies."""
    issues = {
        'deprecated_variables': [],
        'deprecated_formats': [],
        'missing_position_type': [],
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return issues
    
    # Scan for deprecated variable names
    for var_name in DEPRECATED_VARIABLE_NAMES:
        # Look for variable declarations/usage
        pattern = rf'\b{var_name}\b'
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line):
                # Exclude comments explaining deprecated patterns
                if 'deprecated' not in line.lower() and 'wrong' not in line.lower():
                    issues['deprecated_variables'].append({
                        'line': i,
                        'content': line.strip(),
                        'variable': var_name
                    })
    
    # Scan for deprecated format patterns
    for pattern in DEPRECATED_FORMATS:
        for i, line in enumerate(lines, 1):
            matches = re.finditer(pattern, line)
            for match in matches:
                # Exclude comments, markdown code blocks, and documentation examples showing wrong patterns
                if ('❌' not in line and '# WRONG' not in line and 
                    'deprecated' not in line.lower() and
                    '```' not in line):
                    issues['deprecated_formats'].append({
                        'line': i,
                        'content': line.strip(),
                        'match': match.group(0),
                        'pattern': pattern
                    })
    
    return issues


def scan_directory(root_path: Path, include_patterns: List[str], exclude_patterns: List[str]) -> Dict:
    """Recursively scan directory for issues."""
    all_issues = {}
    
    for root, dirs, files in os.walk(root_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not any(ex in str(Path(root) / d) for ex in exclude_patterns)]
        
        for file in files:
            filepath = Path(root) / file
            
            # Check if file matches include patterns
            if not any(filepath.match(pattern) for pattern in include_patterns):
                continue
            
            # Skip excluded patterns
            if any(ex in str(filepath) for ex in exclude_patterns):
                continue
            
            issues = scan_file(filepath)
            if any(issues.values()):
                rel_path = filepath.relative_to(root_path)
                all_issues[str(rel_path)] = issues
    
    return all_issues


def generate_report(results: Dict) -> str:
    """Generate human-readable report."""
    report = []
    report.append("=" * 80)
    report.append("INSTRUMENT KEY FORMAT INCONSISTENCY SCAN REPORT")
    report.append("=" * 80)
    report.append(f"\nScanned codebase for deviations from canonical format: venue:position_type:symbol\n")
    
    total_files = len(results)
    total_deprecated_vars = sum(len(r['deprecated_variables']) for r in results.values())
    total_deprecated_formats = sum(len(r['deprecated_formats']) for r in results.values())
    total_missing_type = sum(len(r['missing_position_type']) for r in results.values())
    
    report.append(f"Summary:")
    report.append(f"  Files with issues: {total_files}")
    report.append(f"  Deprecated variable names: {total_deprecated_vars}")
    report.append(f"  Deprecated format patterns: {total_deprecated_formats}")
    report.append(f"  Missing position_type: {total_missing_type}")
    report.append("")
    
    if total_files == 0:
        report.append("✅ No inconsistencies found! All code follows canonical format.")
        return "\n".join(report)
    
    # Group by issue type
    report.append("\n" + "=" * 80)
    report.append("DETAILED FINDINGS")
    report.append("=" * 80)
    
    for filepath, issues in sorted(results.items()):
        report.append(f"\n📁 {filepath}")
        report.append("-" * 80)
        
        if issues['deprecated_variables']:
            report.append("\n  ⚠️  DEPRECATED VARIABLE NAMES:")
            for issue in issues['deprecated_variables'][:10]:  # Limit to first 10
                report.append(f"    Line {issue['line']}: {issue['variable']}")
                report.append(f"      {issue['content'][:100]}")
            if len(issues['deprecated_variables']) > 10:
                report.append(f"    ... and {len(issues['deprecated_variables']) - 10} more")
        
        if issues['deprecated_formats']:
            report.append("\n  ⚠️  DEPRECATED FORMAT PATTERNS:")
            for issue in issues['deprecated_formats'][:10]:
                report.append(f"    Line {issue['line']}: '{issue['match']}'")
                report.append(f"      {issue['content'][:100]}")
            if len(issues['deprecated_formats']) > 10:
                report.append(f"    ... and {len(issues['deprecated_formats']) - 10} more")
        
        if issues['missing_position_type']:
            report.append("\n  ⚠️  MISSING POSITION TYPE:")
            for issue in issues['missing_position_type'][:10]:
                report.append(f"    Line {issue['line']}: {issue['match']}")
                report.append(f"      {issue['content'][:100]}")
            if len(issues['missing_position_type']) > 10:
                report.append(f"    ... and {len(issues['missing_position_type']) - 10} more")
    
    report.append("\n" + "=" * 80)
    report.append("RECOMMENDED ACTIONS")
    report.append("=" * 80)
    report.append("\n1. Replace deprecated variable names:")
    report.append("   instrument_id → position_key")
    report.append("   instrument_key → position_key")
    report.append("   position_id → position_key")
    report.append("\n2. Update deprecated format patterns:")
    report.append("   wallet.USDT → wallet:BaseToken:USDT")
    report.append("   binance:BTC → binance:BaseToken:BTC")
    report.append("   binance_BTC_USDT → binance:Perp:BTCUSDT")
    report.append("\n3. Add missing position_type:")
    report.append("   binance:USDT → binance:BaseToken:USDT")
    report.append("   aave:aUSDT → aave_v3:aToken:aUSDT")
    report.append("")
    
    return "\n".join(report)


def main():
    """Main scanning logic."""
    repo_root = Path(__file__).parent.parent
    
    # Scan configurations
    scan_configs = [
        {
            'name': 'Backend Python Code',
            'path': repo_root / 'backend',
            'include': ['*.py'],
            'exclude': ['__pycache__', '.pyc', 'venv', '.egg-info']
        },
        {
            'name': 'Frontend TypeScript Code',
            'path': repo_root / 'frontend',
            'include': ['*.ts', '*.tsx'],
            'exclude': ['node_modules', 'dist', 'build']
        },
        {
            'name': 'Configuration Files',
            'path': repo_root / 'configs',
            'include': ['*.yaml', '*.yml'],
            'exclude': []
        },
        {
            'name': 'Documentation',
            'path': repo_root / 'docs',
            'include': ['*.md'],
            'exclude': ['archive']
        },
        {
            'name': 'Test Files',
            'path': repo_root / 'tests',
            'include': ['*.py'],
            'exclude': ['__pycache__', '.pyc']
        },
        {
            'name': 'Scripts',
            'path': repo_root / 'scripts',
            'include': ['*.py'],
            'exclude': []
        }
    ]
    
    all_results = {}
    
    print("🔍 Scanning codebase for instrument key inconsistencies...\n")
    
    for config in scan_configs:
        print(f"Scanning: {config['name']}...")
        if not config['path'].exists():
            print(f"  ⚠️  Path not found: {config['path']}")
            continue
        
        results = scan_directory(
            config['path'],
            config['include'],
            config['exclude']
        )
        
        if results:
            all_results[config['name']] = results
            print(f"  Found issues in {len(results)} files")
        else:
            print(f"  ✅ No issues found")
    
    print("\n" + "=" * 80)
    print("Generating report...")
    
    # Flatten results for report
    flat_results = {}
    for section_name, section_results in all_results.items():
        for filepath, issues in section_results.items():
            flat_results[f"{section_name}/{filepath}"] = issues
    
    report = generate_report(flat_results)
    
    # Write to file
    output_file = repo_root / 'instrument_key_INCONSISTENCIES_REPORT.md'
    with open(output_file, 'w') as f:
        f.write(report)
    
    print(f"\n📄 Report written to: {output_file}")
    print("\nPreview:")
    print(report[:2000])
    if len(report) > 2000:
        print(f"\n... (truncated, see full report in file)")
    
    # Also save JSON for programmatic processing
    json_file = repo_root / 'instrument_key_inconsistencies.json'
    with open(json_file, 'w') as f:
        json.dump(flat_results, f, indent=2)
    
    print(f"\n📊 JSON data written to: {json_file}")
    
    return len(flat_results)


if __name__ == '__main__':
    issue_count = main()
    exit(0 if issue_count == 0 else 1)


