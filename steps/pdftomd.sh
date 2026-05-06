#!/usr/bin/env bash

set -u

convert_pdf_to_md() {
    TMP_FILE=$(mktemp)

    pdftotext -layout -enc UTF-8 $1 "$TMP_FILE"

    ZWS="​"

    UL_MARK="●"
    UL_MARK_2="○"
    UL_MARK_3="▫️"

    HEADER=$(awk 'BEGIN {RS=""; ORS=""} NR==1 {print; exit}' "$TMP_FILE")

    # Create header
    sed -i "1s/^/# /" "$TMP_FILE"

    # Remove header at page breaks using perl for multiline matching
    perl -i -0777 -pe "s/\x0c\s*\Q$HEADER\E//g" "$TMP_FILE"

    # Find hard line breaks and replace them with spaces, but preserve structural hierarchy
    CLEAN_TEXT=$(awk -v RS='' -v ORS='\n\n' '{
        n = split($0, lines, "\n");
        result = "";
        for (i = 1; i <= n; i++) {
            line = lines[i];
            if (line ~ /^[ \t]*$/) continue;

            if (result == "") {
                result = line;
                continue;
            }

            # If current line starts with a bullet, digit-list, or point-label (allowing indentation)
            if (line ~ /^[ \t]*([●○▫️•*-]|[0-9]+\.|\([0-9]+ балл?а?і?в?\))/) {
                result = result "\n" line;
                continue;
            }

            # Continuation line: join with previous. Trim leading spaces of continuation.
            sub(/^[ \t]+/, "", line);
            result = result " " line;
        }
        print result;
    }' "$TMP_FILE")

    # 2. Write it back to the file (safely quoted!)
    printf '%s\n' "$CLEAN_TEXT" > "$TMP_FILE"

    # Place all ordered list markers on a new line, preserving indentation
    sed -E -i 's/([^ ])([ \t]+(([0-9]+\.)+)+ )/\1\n\2/g' "$TMP_FILE"

    # Replace unordered list markers with a dash, preserving indentation
    sed -E -i "s/([ \t]*)[$UL_MARK$UL_MARK_2$UL_MARK_3]$ZWS?/\1- /g" "$TMP_FILE"

    # Remove zws or page breaks
    sed -E -i "s/$ZWS|\x0c//g" "$TMP_FILE"

    # Ensure 'Разом:' is on its own line if it got joined, preserving indentation
    sed -E -i 's/ (Разом: [0-9]+ бали?і?в?)/\n\1/g' "$TMP_FILE"

    # Add newline before '(\d+ бал...)' if it got joined mid-line
    sed -E -i 's/([^ -]) ?(\([0-9]+ балл?а?і?в?\))/\1\n\2/g' "$TMP_FILE"

    # Add newline after '.' in unordered list to split items if they were joined
    sed -E -i 's/(\s+-.+\.) (.+)/\1\n\2/g' "$TMP_FILE"

    # Remove multiple spaces between words (but NOT leading spaces)
    sed -E -i "s/([^ ])[ \t]{2,}/\1 /g" "$TMP_FILE"

    mv "$TMP_FILE" "$2"
}

for pdf in $(dirname $0)/pdfs/*.pdf; do
    NUM=$(grep -oP '\d+' <<< "$pdf")
    NEW_NAME=$(printf "$(dirname $0)/proj-step-%02d.md" "$((10#$NUM))")

    convert_pdf_to_md "$pdf" "$NEW_NAME"
done
