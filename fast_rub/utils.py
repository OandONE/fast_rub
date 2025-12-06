import re
from typing import List, Dict, Any, Tuple, Optional


def _collect_matches(text: str, patterns: Dict[str, List[str]], priority: Dict[str, int]) -> List[Dict[str, Any]]:
    matches = []
    for style, pats in patterns.items():
        for pat in pats:
            for m in re.finditer(pat, text, flags=re.DOTALL | re.MULTILINE):
                start, end = m.start(), m.end()
                groups = m.groups()
                content = ""
                extra = None

                if style == "Link" and len(groups) >= 2:
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

def _allow_match(chosen: List[Dict[str, Any]], candidate: Dict[str, Any]) -> bool:
    s, e = candidate["start"], candidate["end"]
    for c in chosen:
        os, oe = c["start"], c["end"]
        if (s >= os and e <= oe) or (os >= s and oe <= e):
            continue
        if not (e <= os or s >= oe):
            return False
    return True

def _pick_matches_allowing_nested(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    matches_sorted = sorted(matches, key=lambda m: (m['priority'], m['start']))
    chosen = []
    for m in matches_sorted:
        if _allow_match(chosen, m):
            chosen.append(m)
    chosen.sort(key=lambda m: m['start'])
    return chosen

class TextParser:
    @staticmethod
    def checkMarkdown(text: str) -> Tuple[List[Dict[str, Any]], str]:
        """
        Parse Markdown and return flat metadata list + plain text.
        - Nested styles are preserved as separate metadata entries (flat list).
        - Partial/cross overlaps are rejected.
        """
        if not text:
            return [], ""

        patterns = {
            "Pre": [r"```(?:[^\n]*\n)?([\s\S]*?)```"],
            "Link": [r"\[([^\]]+?)\]\(([^)]+?)\)"],  # [text](url)
            "MentionMD": [r"@@([^@]+?)@@"],
            "CodeInline": [r"`([^`]+?)`"],
            "Spoiler": [r"\|\|([^|]+?)\|\|"],
            "Bold": [r"\*\*([^\*]+?)\*\*", r"__(?<!_)([^_]+?)__(?!_)"],
            "Strike": [r"~~([^~]+?)~~"],
            "Underline": [r"__(?<!_)([^_]+?)__(?!_)"],
            "Italic": [r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"(?<!_)_([^_\n]+?)_(?!_)"],
            "Blockquote": [r"(^> .+(?:\n> .+)*)"]
        }

        priority = {
            "Pre": 0,
            "Link": 1,
            "MentionMD": 1,
            "CodeInline": 2,
            "Spoiler": 3,
            "Bold": 4,
            "Strike": 5,
            "Underline": 6,
            "Italic": 7,
            "Blockquote": 8
        }

        all_matches = _collect_matches(text, patterns, priority)
        chosen = _pick_matches_allowing_nested(all_matches)

        out_parts: List[str] = []
        metadata: List[Dict[str, Any]] = []
        last = 0

        for m in chosen:
            if last < m['start']:
                out_parts.append(text[last:m['start']])
            current_index = sum(len(p) for p in out_parts)
            out_parts.append(m['content'])
            length = len(m['content'])
            st = m['style']

            if st == "Link":
                metadata.append({
                    "type": "Link",
                    "from_index": current_index,
                    "length": length,
                    "link_url": m['extra']
                })
            elif st == "MentionMD":
                metadata.append({
                    "type": "MentionText",
                    "from_index": current_index,
                    "length": length,
                    "mention_text_object_guid": m['content'],
                    "mention_text_user_id": m['content'],
                    "mention_text_object_type": "user"
                })
            elif st == "CodeInline":
                metadata.append({
                    "type": "Mono",
                    "from_index": current_index,
                    "length": length
                })
            elif st == "Pre":
                metadata.append({
                    "type": "Pre",
                    "from_index": current_index,
                    "length": length
                })
            elif st == "Blockquote":
                lines = re.sub(r"^> ?", "", m['content'], flags=re.MULTILINE)
                metadata.append({
                    "type": "Blockquote",
                    "from_index": current_index,
                    "length": length
                })
            else:
                map_types = {
                    "Bold": "Bold",
                    "Italic": "Italic",
                    "Underline": "Underline",
                    "Strike": "Strike",
                    "Spoiler": "Spoiler"
                }
                meta_type = map_types.get(st, st)
                metadata.append({
                    "type": meta_type,
                    "from_index": current_index,
                    "length": length
                })

            last = m['end']

        if last < len(text):
            out_parts.append(text[last:])

        real_text_final = "".join(out_parts)
        return metadata, real_text_final

    @staticmethod
    def checkHTML(text: str) -> Tuple[List[Dict[str, Any]], str]:
        """
        Parse simple HTML-like tags and return flat metadata + plain text.
        Supports <b>, <strong>, <i>, <em>, <code>, <s>, <del>, <u>, <pre>, <span class="tg-spoiler">,
        <a href="...">text</a>, <mention objectId="...">text</mention>, and rubika:// links.
        """
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
        }

        priority = {
            "PreHTML": 0,
            "HTMLLink": 1,
            "MentionHTML": 1,
            "CodeInlineHTML": 2,
            "SpoilerHTML": 3,
            "BoldHTML": 4,
            "ItalicHTML": 5,
            "StrikeHTML": 6,
            "UnderlineHTML": 7
        }

        all_matches = _collect_matches(text, patterns, priority)
        chosen = _pick_matches_allowing_nested(all_matches)

        out_parts: List[str] = []
        metadata: List[Dict[str, Any]] = []
        last = 0

        for m in chosen:
            if last < m['start']:
                out_parts.append(text[last:m['start']])
            current_index = sum(len(p) for p in out_parts)
            out_parts.append(m['content'])
            length = len(m['content'])
            st = m['style']

            if st == "HTMLLink":
                url = m['extra']
                if url and url.startswith("rubika://"):
                    uid = url.replace("rubika://", "")
                    metadata.append({
                        "type": "MentionText",
                        "from_index": current_index,
                        "length": length,
                        "mention_text_object_guid": uid,
                        "mention_text_user_id": uid,
                        "mention_text_object_type": "user"
                    })
                else:
                    metadata.append({
                        "type": "Link",
                        "from_index": current_index,
                        "length": length,
                        "link_url": url
                    })
            elif st == "MentionHTML":
                object_id = m['extra'] or m['content']
                metadata.append({
                    "type": "MentionText",
                    "from_index": current_index,
                    "length": length,
                    "mention_text_object_guid": object_id,
                    "mention_text_user_id": object_id,
                    "mention_text_object_type": "group"
                })
            elif st == "CodeInlineHTML":
                metadata.append({
                    "type": "Mono",
                    "from_index": current_index,
                    "length": length
                })
            elif st == "PreHTML":
                metadata.append({
                    "type": "Pre",
                    "from_index": current_index,
                    "length": length
                })
            elif st == "SpoilerHTML":
                metadata.append({
                    "type": "Spoiler",
                    "from_index": current_index,
                    "length": length
                })
            else:
                map_html = {
                    "BoldHTML": "Bold",
                    "ItalicHTML": "Italic",
                    "UnderlineHTML": "Underline",
                    "StrikeHTML": "Strike"
                }
                meta_type = map_html.get(st, st)
                metadata.append({
                    "type": meta_type,
                    "from_index": current_index,
                    "length": length
                })

            last = m['end']

        if last < len(text):
            out_parts.append(text[last:])

        real_text_final = "".join(out_parts)
        return metadata, real_text_final

class utils:
    @staticmethod
    def format_file(type_file: Optional[str] = None) -> Optional[str]:
        if not type_file:
            return None
        for type_,pass_ in {"File":"", "Image":".png", "Voice":".mp3", "Music":".mp3", "Gif":".png" , "Video":".mp4"}.items():
            if type_ == type_file:
                name_file = type_+pass_
                return name_file
        return None