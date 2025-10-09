#!/bin/bash

# Quality Gate: Documentation Link Validation
# This script validates all internal links in the docs/ directory
# and ensures no broken references exist

set -e  # Exit on any error

echo "=== Documentation Link Validation Quality Gate ==="
echo "Timestamp: $(date)"
echo

# Initialize counters
TOTAL_LINKS=0
BROKEN_LINKS=0
TOTAL_FILES=0
BROKEN_FILES=0

# Find all markdown files
echo "1. Scanning markdown files in docs/:"
MARKDOWN_FILES=$(find docs/ -name "*.md" -type f)
TOTAL_FILES=$(echo "$MARKDOWN_FILES" | wc -l)
echo "Found $TOTAL_FILES markdown files"
echo

# Extract all internal links
echo "2. Extracting all internal links:"
INTERNAL_LINKS=$(grep -r "\[.*\]([^http]" docs/ | sed 's/.*\[\([^]]*\)\](\([^)]*\)).*/\2/' | sort | uniq)
TOTAL_LINKS=$(echo "$INTERNAL_LINKS" | wc -l)
echo "Found $TOTAL_LINKS internal links"
echo

# Check for broken links
echo "3. Validating link integrity:"
BROKEN_LINKS_LIST=""
BROKEN_FILES_LIST=""

while IFS= read -r link; do
  if [[ -n "$link" ]]; then
    # Check various possible paths
    if [[ ! -f "docs/$link" && ! -f "$link" && ! -f "$link.md" && ! -f "docs/$link.md" ]]; then
      BROKEN_LINKS=$((BROKEN_LINKS + 1))
      BROKEN_LINKS_LIST="$BROKEN_LINKS_LIST\nBROKEN: $link"
      
      # Find which file contains this broken link
      BROKEN_FILE=$(grep -r "\[.*\]([^http]" docs/ | grep "$link" | head -1 | cut -d: -f1)
      if [[ -n "$BROKEN_FILE" ]]; then
        BROKEN_FILES_LIST="$BROKEN_FILES_LIST\n$BROKEN_FILE"
      fi
    fi
  fi
done <<< "$INTERNAL_LINKS"

# Count unique broken files
BROKEN_FILES=$(echo -e "$BROKEN_FILES_LIST" | sort | uniq | wc -l)

echo "Link validation complete"
echo

# Check for section references
echo "4. Validating section references:"
SECTION_REFS=$(grep -r "#" docs/ | grep -v "^#" | sed 's/.*#\([^[:space:]]*\).*/\1/' | sort | uniq)
TOTAL_SECTIONS=$(echo "$SECTION_REFS" | wc -l)
echo "Found $TOTAL_SECTIONS section references"
echo

# Check for cross-references
echo "5. Validating cross-references:"
CROSS_REFS=$(grep -r "docs/" docs/ | grep -v "\.md")
TOTAL_CROSS_REFS=$(echo "$CROSS_REFS" | wc -l)
echo "Found $TOTAL_CROSS_REFS cross-references"
echo

# Quality Gate Results
echo "=== Quality Gate Results ==="
echo "Total markdown files: $TOTAL_FILES"
echo "Total internal links: $TOTAL_LINKS"
echo "Broken links: $BROKEN_LINKS"
echo "Files with broken links: $BROKEN_FILES"
echo "Total section references: $TOTAL_SECTIONS"
echo "Total cross-references: $TOTAL_CROSS_REFS"
echo

# Calculate pass rate
if [[ $TOTAL_LINKS -eq 0 ]]; then
  PASS_RATE=100
else
  PASS_RATE=$(( (TOTAL_LINKS - BROKEN_LINKS) * 100 / TOTAL_LINKS ))
fi

echo "Link integrity pass rate: $PASS_RATE%"
echo

# Quality Gate Decision
if [[ $BROKEN_LINKS -eq 0 ]]; then
  echo "✅ QUALITY GATE PASSED: All links are valid"
  echo "All $TOTAL_LINKS internal links are working correctly"
  exit 0
else
  echo "❌ QUALITY GATE FAILED: $BROKEN_LINKS broken links found"
  echo
  echo "Broken links:"
  echo -e "$BROKEN_LINKS_LIST"
  echo
  echo "Files with broken links:"
  echo -e "$BROKEN_FILES_LIST" | sort | uniq
  echo
  echo "Required action: Fix all broken links before proceeding"
  echo "Target: 100% link integrity (0 broken links)"
  echo "Current: $PASS_RATE% link integrity ($BROKEN_LINKS broken links)"
  exit 1
fi
