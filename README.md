# wordlistdawg

Offline dictionary build pipeline:

1. `SCOWLv2` source -> normalized lowercase `words.txt`
2. `Collins Scrabble Words (CSW21)` merged in -> deduplicated `words.txt`
3. `words.txt` -> packed DAWG `dict.dawg`
4. Browser runtime uses `src/dict.ts` with no backend

## Output files

### `words.txt`

Plain text file with one word per line, sorted alphabetically. Contains ~291k normalized English words (lowercase a-z only, no hyphens, accents, or apostrophes). Combines two sources:

- **SCOWL v2** (size 80) — general English words across US/UK/CA/AU spellings. Proper nouns and abbreviations are excluded by filtering to lowercase-only entries in the raw SCOWL output.
- **Collins Scrabble Words 2021 (CSW21)** — the international Scrabble dictionary (SOWPODS), adding ~100k additional words not in SCOWL.

### `dict.dawg`

Packed DAWG (Directed Acyclic Word Graph) binary built from `words.txt` using the `dawg-lookup` library. This is a compressed trie structure (~577 KB) that supports fast `isWord` and `isPrefix` lookups without loading the full word list into memory. Used by the runtime API in `src/dict.ts`.

### `dict.meta.json`

Metadata about the sources, build profile, word count stats, and DAWG artifact checksums.

## Sources

- **SCOWL**: `https://github.com/en-wl/wordlist` (`v2`), pinned commit `744c09288...`
  - Size: `80`, Spellings: `A,B,Z,C,D` (US/UK/CA/AU), core words only
  - Normalization: filter to lowercase-only entries, then strip non-`a-z`
- **CSW21**: Collins Scrabble Words 2021 via `scrabblewords/scrabblewords` on GitHub
  - Normalized to lowercase a-z to match SCOWL format

## Build commands

```bash
npm install

# SCOWL-only build:
npm run dict:build        # dict:words + dict:dawg

# Full build (SCOWL + Scrabble merge + DAWG):
npm run dict:build-full   # dict:words + dict:merge-scrabble + dict:dawg
```

Individual steps:

```bash
npm run dict:words            # fetch SCOWL, normalize -> words.txt
npm run dict:merge-scrabble   # download CSW21, merge into words.txt
npm run dict:dawg             # words.txt -> dict.dawg
```

`dict:words` downloads a pinned SCOWLv2 archive. On the first successful download, it records a checksum lock at `data/scowl/source.lock.json`; subsequent runs verify against that checksum. `dict:merge-scrabble` downloads CSW21 once and caches it at `data/scrabble/csw21.txt`.

## Runtime API

`src/dict.ts` exports:

- `loadDictionary(metaUrl?: string): Promise<void>`
- `normalizeWord(input: string): string`
- `isWord(word: string): boolean`
- `isPrefix(prefix: string): boolean`

## Tests

```bash
npm run dict:test
```

## Attribution

Word list data is derived from SCOWL/SCOWLv2 (`en-wl/wordlist`) and Collins Scrabble Words 2021 (`scrabblewords/scrabblewords`). Keep the included SCOWL license and copyright notices with distributed dictionary artifacts.
