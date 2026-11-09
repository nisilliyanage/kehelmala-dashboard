# config.py
# All hand-made judgment calls live here (or in data/processed/manual_group_merges.json
# for merges made via the CLI tool) so they survive re-running the pipeline on fresh
# weekly CSV/XLSX exports. Edit freely; nothing here is overwritten by the pipeline.

# YouTube Shorts are capped at this duration by YouTube itself. Used only as a last-resort
# signal; the primary Short/Standard heuristic is view-rank based (see src/cluster_videos.py).
SHORT_MAX_SEC = 183

# Words ignored when computing title similarity between platforms.
STOPWORDS = {
    'a', 'an', 'the', 'kehelmala', 'short', 'shorts', 'viral', 'explore',
    'exploremore', 'explorepage', 'creative', 'storytelling', 'fyp',
    'foryou', 'foryoupage', 'trending', 'more', 'video', 'film', 'films',
    'studios', 'viralvideo', 'fypage', 'and', 'of', 'to',
    'pt', 'part', 'episode', 'ep',
}

# Minimum Jaccard word-overlap score for two titles to be considered a match.
JACCARD_MATCH_THRESHOLD = 0.4

# Minimum word length considered for the "one title contains the other" exception.
CONTAINMENT_MIN_WORD_LEN = 4

# Hand-verified cross-platform merges that the automatic matcher can't find on its own
# (e.g. a caption that's pure hashtags, or titles written in different scripts).
# 'match' is a list of substrings — if a post's raw title/caption contains ANY of these
# (case-insensitive), it's pulled into the group named 'title'.
# NOTE: prefer merging via `python src/merge_videos_cli.py` going forward — it writes to
# data/processed/manual_group_merges.json instead, which is easier to manage as the list
# grows. Entries below are kept for historical/manual edits.
MANUAL_TITLE_MERGES = [
    {'match': ['snake bag', 'handbag problems'], 'title': 'Snake Bag (Handbag Problems)'},
    {'match': ['#younglove', 'sneaking in'], 'title': 'Sneaking In'},
    # Social posts call these "Caller Unknown" (2024), YouTube calls them "Wrong Number"
    # (2025). The sequel comes first so "Caller Unknown 2" doesn't hit the plain rule.
    {'match': ['interrogation', 'caller unknown 2', 'wrong number 2'], 'title': 'Interrogation (Wrong Number 2)'},
    {'match': ['caller unknown', 'wrong number'], 'title': 'Wrong Number'},
    # Granny's Story (2024) and Granny, No! (2025) are separate projects; the matcher
    # pulls the curly-apostrophe "Granny’s Story" posts into Granny, No!.
    {'match': ["granny's story", 'granny’s story'], 'title': "Granny's Story"},
    # Chocolate is a 4-part series - one row per part. The matcher lumps them together
    # (and Facebook's "last episode" ends up on its own), so each part is pinned here.
    # TikTok's Part 3 is captioned only "Replying to @K_ax" (confirmed Part 3).
    {'match': ['chocolate, final episode', 'chocolate - last episode'], 'title': 'Chocolate - Part 4'},
    {'match': ['chocolate - part 3', 'chocolate, pt 3', 'replying to @k_ax'], 'title': 'Chocolate - Part 3'},
    {'match': ['chocolate - part 2', 'chocolate, pt 2', 'chocolate, part 2'], 'title': 'Chocolate - Part 2'},
    {'match': ['chocolate - part 1', 'chocolate, part 1', 'chocolate, part one'], 'title': 'Chocolate - Part 1'},
]

# Permalinks to exclude outright (pass the Post-type filter but aren't original video content).
MANUAL_EXCLUDE_PERMALINKS = {
    'https://www.facebook.com/kehelmalastudios/posts/pfbid02fyWYLobsYdJs11joqjvzkJdDN8GQa37rZJknE6cW6UVZMgTw3ZeyqPnVdz1ZrrQvl',
}

# Posts whose raw title/caption contains any of these (case-insensitive) are left out
# on every platform - e.g. behind-the-scenes clips, which aren't the video itself.
MANUAL_EXCLUDE_TITLE_PHRASES = ['behind the scenes']

# Hand-fixed display titles, e.g. for posts whose only title is in Sinhala/Tamil script.
# Key = the raw title/caption text exactly as it appears in the source export.
MANUAL_TITLE_TEXT_FIXES = {
    # 'කොළ අතර අභිරහස': 'Put the real English title here once you know it',
}

# Rename or alter any video's final display title on the dashboard.
# Key = current title as it appears on the dashboard (case-insensitive).
# Value = new title you want displayed.
# Example:
# TITLE_RENAMES = {
#     'Behave': 'Behave!',
#     'කොළ අතර අභිරහස': 'A Fertile Mystery',
# }
TITLE_RENAMES = {
    'Snake Bag Handbag Problems': 'Snake Bag (Handbag Problems)',
    "What s with Su": "What's with Su",
    'Dodol pt 2': 'Dodol',
    'Gift Box Pt 2': 'Gift Box',
    'Pinipa pt 2': 'Pinipa',
    "What's with Su Trick or Treat" : "What's with Su (Trick or Treat)",
    "Who s winning": "Who's winning",
    'Gift': 'The Gift',
    'Santa s Gift': "Santa's Gift",
    'Face Off Produced in partnership with Closeup': 'Face Off',
    'Wrong Number': 'Wrong Number (Caller Unknown)',
}   