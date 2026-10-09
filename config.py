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
]

# Permalinks to exclude outright (pass the Post-type filter but aren't original video content).
MANUAL_EXCLUDE_PERMALINKS = {
    'https://www.facebook.com/kehelmalastudios/posts/pfbid02fyWYLobsYdJs11joqjvzkJdDN8GQa37rZJknE6cW6UVZMgTw3ZeyqPnVdz1ZrrQvl',
}

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
}   