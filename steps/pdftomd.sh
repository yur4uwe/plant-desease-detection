#!/usr/bin/env bash

set -u

convert_pdf_to_md() {
    TMP_FILE=$(mktemp)

    pdftotext -enc UTF-8 -layout $1 "$TMP_FILE"

    ZWS="​"

    UL_MARK="●"

    UL_MARK_2="○"

    HEADER=$(head -n 1 "$TMP_FILE")

    # Create header
    sed -i '1s/^/# /' "$TMP_FILE"

    # Remove header at the page break
    sed -i "s/\x0c$HEADER//g" "$TMP_FILE"

    # Find hard line breaks and replace them with spaces
    # 1. Do the awk magic and hold the result in memory
    CLEAN_TEXT=$(awk -v RS='' -v ORS='\n\n' '{ gsub(/\n/, " "); print }' "$TMP_FILE")

    # 2. Write it back to the file (safely quoted!)
    printf '%s\n' "$CLEAN_TEXT" > "$TMP_FILE"

    # Place all ordered list markers on a new line
    sed -E -i 's/([^ ]+)\s*(([0-9]+\.)+) /\1\n\2 /g' "$TMP_FILE"

    # Replace unordered list markers with a dash
    sed -E -i "s/(\s+)$UL_MARK$ZWS/\n\1-/g" "$TMP_FILE"

    # Replace unordered list second level markers with a dash and 8 spaces
    sed -E -i "s/(\s+)$UL_MARK_2$ZWS/\1\n        -/g" "$TMP_FILE"

    sed -E -i "s/(\s+) -$ZWS/\n\1-/g" "$TMP_FILE"

    # Remove multiple spaces between words
    sed -E -i "s/([^\x20])\x20+/\1 /g" "$TMP_FILE"

    # Remove hard newline if not dot and the end of the line
    sed -E -i "s/([^\.])\n$/\1/g" "$TMP_FILE"

    mv "$TMP_FILE" "$2"
}

for pdf in $(dirname $0)/*.pdf; do
    NUM=$(grep -oP '\d+' <<< "$pdf")
    NEW_NAME=$(printf "proj-step-%02d.md" "$NUM")

    convert_pdf_to_md "$pdf" "$NEW_NAME"
done
