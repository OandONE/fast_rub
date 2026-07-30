import re
from typing import Any


def _build_utf16_prefix_lengths(text: str) -> list[int]:
    """آرایه طول‌های تجمعی UTF-16 برای هر کاراکتر"""
    prefix = [0]
    total = 0
    for char in text:
        total += 2 if ord(char) > 0xFFFF else 1
        prefix.append(total)
    return prefix


def _collect_matches(text: str, patterns: dict[str, list[str]], priority: dict[str, int]) -> list[dict[str, Any]]:
    matches = []
    for style, pats in patterns.items():
        for pat in pats:
            for m in re.finditer(pat, text, flags=re.DOTALL | re.MULTILINE):
                start, end = m.start(), m.end()
                groups = m.groups()
                content = ""
                extra = None

                if style in ["Link", "Mention"] and len(groups) >= 2:
                    content = groups[0]
                    extra = groups[1]
                elif style == "HTMLLink" and len(groups) >= 2:
                    extra = groups[0]
                    content = groups[1]
                elif style == "MentionHTML" and len(groups) >= 2:
                    extra = groups[0]
                    content = groups[1]
                else:
                    if len(groups) >= 1:
                        content = groups[0]
                    else:
                        content = m.group(0)

                if style in ("Pre", "PreHTML"):
                    content = content.strip("\n")
                
                if style == "Quote":
                    lines = content.split("\n")
                    clean_lines = []
                    for line in lines:
                        if line.startswith("> "):
                            clean_lines.append(line[2:])
                        elif line.startswith(">"):
                            clean_lines.append(line[1:])
                        else:
                            clean_lines.append(line)
                    content = "\n".join(clean_lines)

                matches.append({
                    "start": start,
                    "end": end,
                    "style": style,
                    "content": content,
                    "full_match": m.group(0),
                    "extra": extra,
                    "priority": priority.get(style, 50)
                })
    return matches


def _allow_match(chosen: list[dict[str, Any]], candidate: dict[str, Any]) -> bool:
    s, e = candidate["start"], candidate["end"]
    for c in chosen:
        os, oe = c["start"], c["end"]
        if (s >= os and e <= oe) or (os >= s and oe <= e):
            continue
        if not (e <= os or s >= oe):
            return False
    return True


def _pick_matches_allowing_nested(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches_sorted = sorted(matches, key=lambda m: (m['priority'], m['start']))
    chosen = []
    for m in matches_sorted:
        if _allow_match(chosen, m):
            chosen.append(m)
    chosen.sort(key=lambda m: m['start'])
    return chosen


class TextParser:
    @staticmethod
    def markdown(text: str) -> tuple[list[dict[str, Any]], str]:
        if not text:
            return [], ""

        patterns = {
            "Pre": [r"```(?:[^\n]*\n)?([\s\S]*?)```"],
            "Link": [r"\[([^\]]+?)\]\((https?://[^)]+)\)"],
            "Mention": [r"\[([^\]]+?)\]\((u[a-zA-Z0-9]+)\)"],
            "CodeInline": [r"`([^`]+?)`"],
            "Spoiler": [r"\|\|([^|]+?)\|\|"],
            "Bold": [r"\*\*([^\*]+?)\*\*"],
            "Strike": [r"~~([^~]+?)~~"],
            "Underline": [r"__([^_]+?)__"],
            "Italic": [r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"(?<!_)_([^_\n]+?)_(?!_)"],
            "Quote": [r"((?:^> [^\n]*(?:\n|$))+)"]
        }

        priority = {
            "Pre": 0, "Link": 1, "Mention": 1, "CodeInline": 2,
            "Spoiler": 3, "Bold": 4, "Strike": 5, "Underline": 6,
            "Italic": 7, "Quote": 8
        }

        all_matches = _collect_matches(text, patterns, priority)

        chosen = _pick_matches_allowing_nested(all_matches)

        utf16_prefix = _build_utf16_prefix_lengths(text)

        out_parts = []
        metadata = []
        last = 0
        offset = 0

        for m in chosen:
            if last < m['start']:
                out_parts.append(text[last:m['start']])
            
            content = m['content']
            st = m['style']
            
            from_index = utf16_prefix[m['start']] - offset
            content_end = m['start'] + len(content)
            length = utf16_prefix[content_end] - utf16_prefix[m['start']]
            
            out_parts.append(content)
            
            full_utf16 = utf16_prefix[m['end']] - utf16_prefix[m['start']]
            offset += full_utf16 - length
            
            last = m['end']
            
            if st == "Link":
                metadata.append({"type": "Link", "from_index": from_index, "length": length, "link_url": m['extra']})
            elif st == "Mention":
                metadata.append({"type": "MentionText", "from_index": from_index, "length": length, "mention_text_object_guid": m['extra'], "mention_text_user_id": m['extra'], "mention_text_object_type": "user"})
            elif st == "CodeInline":
                metadata.append({"type": "Mono", "from_index": from_index, "length": length})
            elif st == "Pre":
                metadata.append({"type": "Pre", "from_index": from_index, "length": length})
            elif st == "Quote":
                metadata.append({"type": "Quote", "from_index": from_index, "length": length})
            else:
                map_types = {"Bold": "Bold", "Italic": "Italic", "Underline": "Underline", "Strike": "Strike", "Spoiler": "Spoiler"}
                metadata.append({"type": map_types.get(st, st), "from_index": from_index, "length": length})

        if last < len(text):
            out_parts.append(text[last:])
        resukt_text = "".join(out_parts)
        return metadata, resukt_text
    
    checkMarkdown = markdown

    @staticmethod
    def html(text: str) -> tuple[list[dict[str, Any]], str]:
        if text is None:
            return [], ""

        patterns = {
            "PreHTML": [r"<pre>([\s\S]*?)</pre>"],
            "HTMLLink": [r'<a\s+href="([^"]+?)">([^<]+?)</a>'],
            "MentionHTML": [r'<mention\s+objectId="([^"]+?)">([^<]+?)</mention>'],
            "CodeInlineHTML": [r"<code>([^<]+?)</code>"],
            "SpoilerHTML": [r'<span\s+class="tg-spoiler">([^<]+?)</span>'],
            "BoldHTML": [r"<b>([^<]+?)</b>", r"<strong>([^<]+?)</strong>"],
            "ItalicHTML": [r"<i>([^<]+?)</i>", r"<em>([^<]+?)</em>"],
            "StrikeHTML": [r"<s>([^<]+?)</s>", r"<del>([^<]+?)</del>"],
            "UnderlineHTML": [r"<u>([^<]+?)</u>"],
            "QuoteHTML": [r"<blockquote>([\s\S]*?)</blockquote>"]
        }

        priority = {
            "PreHTML": 0,
            "HTMLLink": 1, "MentionHTML": 1,
            "CodeInlineHTML": 2,
            "SpoilerHTML": 3,
            "BoldHTML": 4,
            "ItalicHTML": 5,
            "StrikeHTML": 6,
            "UnderlineHTML": 7,
            "QuoteHTML": 8
        }

        all_matches = _collect_matches(text, patterns, priority)
        chosen = _pick_matches_allowing_nested(all_matches)

        utf16_prefix = _build_utf16_prefix_lengths(text)

        out_parts: list[str] = []
        metadata: list[dict[str, Any]] = []
        last_utf8 = 0
        offset_utf16 = 0

        for m in chosen:
            start_utf8 = m['start']
            end_utf8 = m['end']
            content = m['content']
            st = m['style']

            if last_utf8 < start_utf8:
                out_parts.append(text[last_utf8:start_utf8])

            from_index = utf16_prefix[start_utf8] - offset_utf16
            content_end_utf8 = start_utf8 + len(content)
            length = utf16_prefix[content_end_utf8] - utf16_prefix[start_utf8]

            out_parts.append(content)

            full_len_utf16 = utf16_prefix[end_utf8] - utf16_prefix[start_utf8]
            offset_utf16 += full_len_utf16 - length

            last_utf8 = end_utf8

            if st == "HTMLLink":
                url = m['extra']
                if url and url.startswith("rubika://"):
                    uid = url.replace("rubika://", "")
                    metadata.append({"type": "MentionText", "from_index": from_index, "length": length, "mention_text_object_guid": uid, "mention_text_user_id": uid, "mention_text_object_type": "user"})
                else:
                    metadata.append({"type": "Link", "from_index": from_index, "length": length, "link_url": url})
            elif st == "MentionHTML":
                object_id = m['extra'] or m['content']
                metadata.append({"type": "MentionText", "from_index": from_index, "length": length, "mention_text_object_guid": object_id, "mention_text_user_id": object_id, "mention_text_object_type": "group"})
            elif st == "CodeInlineHTML":
                metadata.append({"type": "Mono", "from_index": from_index, "length": length})
            elif st == "PreHTML":
                metadata.append({"type": "Pre", "from_index": from_index, "length": length})
            elif st == "SpoilerHTML":
                metadata.append({"type": "Spoiler", "from_index": from_index, "length": length})
            elif st == "QuoteHTML":
                metadata.append({
                    "type": "Quote",
                    "from_index": from_index,
                    "length": length
                })
            else:
                map_html = {"BoldHTML": "Bold", "ItalicHTML": "Italic", "UnderlineHTML": "Underline", "StrikeHTML": "Strike"}
                metadata.append({"type": map_html.get(st, st), "from_index": from_index, "length": length})

        if last_utf8 < len(text):
            out_parts.append(text[last_utf8:])

        real_text_final = "".join(out_parts)
        return metadata, real_text_final
    
    checkHTML = html
