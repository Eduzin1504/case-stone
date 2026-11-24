# Practitioner and community checklists for detecting and removing "AI slop" (UI, writing, images, social copy)

Research date: 2026-11-23. Local skill files read directly from disk (installed copies) are cited by path; their upstream repos are noted where verified. Items marked [UNVERIFIED] were not confirmed against a primary source in this session.

## 1. Visual/UI tells and fixes

### Takeaway
UI slop follows from "distributional convergence": with no direction, models sample the high-probability center of their training data. The community skills now keep explicit, versioned ban lists, sometimes with exact CSS or hex fingerprints. The canonical tells are: Inter or other default fonts; purple/blue gradients on white; cream/sand body backgrounds with an italic display serif; identical icon+heading+text card grids; an uppercase eyebrow over every section; numbered 01/02/03 markers; the hero-metric template; glassmorphism; gradient text; side-stripe borders; over-rounding; emoji used as icons. The ban lists change over time. Escaping one default (purple SaaS) often lands in the next one (cream editorial serif), and impeccable calls this the "second-order reflex".

### Cited Findings

**Anthropic (Claude blog, "Improving frontend design through skills")**
- Mechanism: "During sampling, models predict tokens based on statistical patterns in training data." Without guidance Claude "samples from this high-probability center". The blog calls this distributional convergence. — [Claude blog](https://www.claude.com/blog/improving-frontend-design-through-skills)
- The default unguided landing page uses Inter fonts, purple gradients on white backgrounds and minimal animation, which "creates what users call the 'AI slop' aesthetic." — [Claude blog](https://www.claude.com/blog/improving-frontend-design-through-skills)
- The skill names fonts to avoid: Inter, Roboto, Arial and system fonts. It also bans "Clichéd color schemes (particularly purple gradients on white backgrounds)", predictable layouts and cookie-cutter components. It warns against converging on the next popular choice, naming Space Grotesk ("it is critical that you think outside the box!"). — [Claude blog](https://www.claude.com/blog/improving-frontend-design-through-skills)
- Positive rules from the same skill:
  - "Pick one distinctive font, use it decisively", with high-contrast pairings and extreme weight and size jumps.
  - "Dominant colors with sharp accents outperform timid, evenly-distributed palettes", using CSS variables.
  - One orchestrated page load with staggered reveals rather than scattered micro-interactions.
  - Backgrounds that build "atmosphere and depth" (layered gradients, geometric patterns) rather than flat solid colors.
  - The skill is about 400 tokens and loads on demand. — [Claude blog](https://www.claude.com/blog/improving-frontend-design-through-skills)

**impeccable (pbakaus/impeccable; local copy `~/.claude/plugins/marketplaces/impeccable/skill/SKILL.src.md`, remote verified as https://github.com/pbakaus/impeccable.git)**
- "Absolute bans" (match-and-refuse):
  - Side-stripe borders: `border-left`/`border-right` over 1px as a colored accent. Fix: a full border, a background tint, a leading number or icon, or nothing.
  - Gradient text: `background-clip: text` with a gradient. Fix: one solid color, with emphasis carried by weight or size.
  - Glassmorphism as a default.
  - The hero-metric template ("Big number, small label, supporting stats, gradient accent. SaaS cliché").
  - Identical card grids (same-size icon + heading + text).
  - A tiny uppercase tracked eyebrow above every section. The skill says it "appears on 55-95% of generations regardless of brief, which is the definition of a tell" (this figure is impeccable's own claim).
  - Numbered section markers (01 / 02 / 03) used as default scaffolding.
  - Text overflowing its container at tablet or mobile widths. — [impeccable repo](https://github.com/pbakaus/impeccable)
- Color rule: "The cream / sand / beige body bg is the saturated AI default of 2026." It defines the band as OKLCH L 0.84–0.97, C < 0.06, hue 40–100. Token names like `--paper`, `--cream`, `--sand`, `--bone`, `--linen`, `--parchment`, `--ivory` "are tells in themselves". Fix: a saturated brand color as the body, a true chroma-0 off-white, or a darker tinted mid-tone. — [impeccable](https://github.com/pbakaus/impeccable)
- Model-specific bans:
  - Codex: the "ghost card" (1px border plus a box-shadow with blur of 16px or more on the same element); `border-radius` of 32px or more on cards ("cards top out at 12–16px"); hand-drawn/sketchy SVG and `feTurbulence` paper grain; `repeating-linear-gradient` stripe backgrounds; decorative CSS grid-line backgrounds; "meta-criticism copy".
  - Gemini: never animate `<img>` on hover (including Tailwind `group-hover:scale`). — [impeccable](https://github.com/pbakaus/impeccable)
- Other rules:
  - Hero clamp max of 6rem or less; display letter-spacing no tighter than -0.04em.
  - "Cards are the lazy answer… Nested cards are always wrong."
  - No bounce or elastic easing; use exponential ease-out.
  - No z-index 999/9999.
  - Avoid a uniform section-fade entrance ("the tell is the uniform reflex").
  - `prefers-reduced-motion` is mandatory. — [impeccable](https://github.com/pbakaus/impeccable)
- "AI slop test": "If someone could look at this interface and say 'AI made that' without doubt, it's failed." The category-reflex check runs at two levels:
  - First-order: could someone guess the palette from the product category alone?
  - Second-order: could someone guess the aesthetic family from the category plus its anti-references, e.g. "AI workflow tool that's not SaaS-cream → editorial-typographic"? — [impeccable](https://github.com/pbakaus/impeccable)
- Font reflex-reject list (`skill/reference/brand.md`): Fraunces, Newsreader, Lora, Crimson (Pro/Text), Playfair Display, Cormorant (Garamond), Syne, IBM Plex Mono/Sans/Serif, Space Mono, Space Grotesk, Inter, DM Sans, DM Serif Display/Text, Outfit, Plus Jakarta Sans, Instrument Sans, Instrument Serif. — [impeccable](https://github.com/pbakaus/impeccable)
- Saturated "aesthetic lane" (2026): Editorial-typographic, meaning a display serif (often italic), small mono labels, ruled separators and monochrome restraint. The fingerprint is "three rule-separated columns, an italic Fraunces / Recoleta / Newsreader headline, lowercase track-spaced metadata, no imagery." — [impeccable](https://github.com/pbakaus/impeccable)
- Font process:
  1. Write down three brand words.
  2. List the three fonts you would pick by reflex and reject any on the list.
  3. Browse real foundries for the brand imagined "as a physical object" (a museum caption, a 1970s terminal manual).
  4. If the final pick matches the original reflex, start over. — [impeccable](https://github.com/pbakaus/impeccable)

**taste-skill (design-taste-frontend; local `~/.claude/skills/taste-skill/SKILL.md`; upstream believed to be leonxlnx/taste-skill [UNVERIFIED repo URL])**
- "Anti-Default Discipline": "Do not default to: AI-purple gradients, centered hero over dark mesh, three equal feature cards, generic glassmorphism on everything, infinite-loop micro-animations everywhere, Inter + slate-900. These are the LLM defaults." — local skill file
- Typography rules:
  - Inter is discouraged as a default; use Geist, Outfit, Cabinet Grotesk or Satoshi.
  - Serif is "very discouraged as the default." The skill calls "creative brief = serif" "the single most-tested AI tell in production rounds."
  - Fraunces and Instrument Serif are banned as defaults ("the two LLM-favorite display serifs").
  - Do not inject a random serif word into a sans headline. — local skill file
- Color rules:
  - "THE LILA RULE": no automatic purple/blue glow.
  - One accent, saturation under 80%, locked across the page.
  - "PREMIUM-CONSUMER PALETTE BAN": cream backgrounds `#f5f1ea #f7f5f1 #fbf8f1 #efeae0 #ece6db #faf7f1 #e8dfcb` and brass/clay/oxblood accents `#b08947 #b6553a #9a2436 #9c6e2a #bc7c3a #7d5621` are banned as defaults. — local skill file
- Emoji policy: discouraged in code, markup and visible text; replace with icon-library glyphs. Hero bans: no tagline under the CTAs, no "Used by engineering teams at…" trust strip, no pricing teaser, no avatar row in the hero. — local skill file

**redesign-skill (same author family; local `~/.claude/skills/redesign-skill/SKILL.md`)**
- Audit checklist, problem then fix:
  - Inter or browser default fonts everywhere.
  - All-caps subheaders everywhere.
  - Pure #000 backgrounds.
  - More than one accent color.
  - "Purple/blue 'AI gradient' aesthetic… the most common AI design fingerprint".
  - "Three equal card columns as feature row. This is the most generic AI layout" (fix: zig-zag, asymmetric grid, masonry).
  - Uniform border-radius everywhere.
  - Everything centered.
  - A left sidebar on every dashboard.
  - Generic card (border + shadow + white).
  - Always one filled button plus one ghost button.
  - Pill "New/Beta" badges.
  - Accordion FAQ.
  - 3-card testimonial carousel with dots.
  - 3-tower pricing.
  - Sun/moon toggle.
  - 4-column footer link farm.
  - Lucide/Feather icons exclusively.
  - Rocketship for "Launch", shield for "Security". — local skill file
- Content tells:
  - "John Doe"/"Acme Corp"/"Nexus"/"SmartFlow".
  - Round fake numbers (99.99%, 50%); the skill suggests messy ones like 47.2%.
  - "Elevate", "Seamless", "Unleash", "Next-Gen", "Game-changer", "Delve", "Tapestry", "In the world of…".
  - "Oops!" errors and exclamation marks in success messages.
  - Lorem ipsum.
  - Title Case On Every Header.
  - Identical blog dates.
  - Stock "diverse team" photos. — local skill file
- "Strategic omissions" AI typically forgets: legal links, a 404 page, form validation, skip link, focus rings, and empty, loading and error states. — local skill file

**Refero anti-ai-slop reference (referodesign/refero_skill)**
- Bans and fixes:
  - Indigo/violet accent ("NEVER… unless the brand explicitly requires it").
  - "Default is NO cards."
  - Dark mode by default.
  - "Calm editorial autopilot" (cream bg, oversized serif headline, one italic serif word, muted earth tones).
  - Emoji as icons.
  - Decorative left accent stripe ("If you can't name its meaning in one word, remove it").
  - Abstract blobs and generic 3D art.
  - Weak CSS fakes of photos. — [refero anti-ai-slop.md](https://raw.githubusercontent.com/referodesign/refero_skill/f78b4eccf112d7a179b92afeafdd7e8684560ac2/references/anti-ai-slop.md)
- Quick tests:
  - Card test: "Remove the border, shadow, background, and radius. If nothing breaks, it wasn't a card."
  - Identity test: could the first viewport belong to another company?
  - Editorial test: "If the hero still works for a coffee shop or hotel, the visual language is too generic."
  - Copy test: "If deleting 30% of copy improves the page → keep deleting." — [refero](https://raw.githubusercontent.com/referodesign/refero_skill/f78b4eccf112d7a179b92afeafdd7e8684560ac2/references/anti-ai-slop.md)

**Others**
- Emil Kowalski skills (`emil-design-eng`, plus `apple-design`) focus mainly on animation, easing and transitions, with some design advice. One review describes its output as a Before/After/Why table. Install: `npx skills@latest add emilkowalski/skills`. — [github.com/emilkowalski/skills](https://github.com/emilkowalski/skills), [Tessl review](https://tessl.io/registry/skills/github/emilkowalski/skills/emil-design-eng/review). The ~55k-star figure comes from a third-party directory and is unverified. — [Enterprise DNA](https://enterprisedna.co/directories/skills/emil-design-eng)
- ui-ux-pro-max (nextlevelbuilder/ui-ux-pro-max-skill) is a data-driven skill. It returns a design system together with industry-filtered anti-patterns, e.g. under accessibility "removing focus rings, icon-only buttons without labels". — [Smithery listing](https://smithery.ai/skills/nextlevelbuilder/ui-ux-pro-max). I did not read its full anti-pattern list.
- Venngage defines AI slop in design as output that is polished at first glance but "lacks originality, context or attention to detail". (Venngage sells AI design tools.) — [Venngage](https://venngage.com/blog/ai-slop-in-design/)

### Inferences
- The lists agree on a core set: purple gradients, Inter, identical 3-card rows, glassmorphism, emoji icons and generic stock/3D imagery. Every source above names at least some of these.
- They also show a drift in the default. Anthropic's 2025 post names purple-on-white plus Inter. The 2026 skills (impeccable, taste-skill, Refero) now treat cream, an italic serif and earth tones as the new saturated default. Any checklist therefore needs dates and periodic revision.
- The fixes work at three levels: (a) deterministic bans with exact CSS or hex fingerprints; (b) process prompts (a physical-scene sentence, three brand words, the reflex-reject step); (c) gestalt tests (the identity, editorial and AI-slop tests).

### Gaps
- No vercel/v0 design guidance document was retrieved, so I can't cite v0-specific rules.
- The eyebrow prevalence figure ("55-95% of generations") is impeccable's own claim; I found no independent measurement.
- I found no peer-reviewed study that measures UI-design tells.

## 2. Writing tells

### Takeaway
Wikipedia's "Signs of AI writing" (WikiProject AI Cleanup) is the de facto taxonomy. It covers content patterns (inflated significance, superficial -ing analysis, vague attributions, "challenges and future outlook" sections), language (era-specific AI vocabulary, copula avoidance, negative parallelisms, rule of three), style (title case, bold, emoji, curly quotes, Markdown), chatbot leftovers, and citation artifacts such as `utm_source=chatgpt.com`. The page warns that detectors and human intuition are both unreliable, and that the real concerns are accuracy, sourcing and neutrality. Kobak et al. give the quantitative backing: at least 13.5% of 2024 PubMed abstracts were LLM-processed.

### Cited Findings

**Wikipedia:Signs of AI writing (fetched Nov 2026; the page is long and evolving)**
- Undue emphasis on significance and legacy: "stands/serves as," "is a testament/reminder," "a crucial/pivotal/vital/key role/moment," "underscores/highlights its importance," "reflects broader," "setting the stage for," "indelible mark." — [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- Notability puffery: "independent coverage," "featured/profiled in," "maintains an active digital presence." — [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- Superficial analyses, usually a trailing present-participle clause: "highlighting/underscoring/emphasizing," "ensuring," "reflecting/symbolizing," "fostering," "valuable insights," "align/resonate with." — [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- Vague attributions: "Industry reports," "Observers have cited," "Experts argue." Outline-like conclusions: "Despite its… faces several challenges," "Future Outlook." — [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- The AI vocabulary list changes by era:
  - 2023–mid-2024: additionally, delve, tapestry, testament, intricate, pivotal, vibrant, garner.
  - Mid-2024–mid-2025: align with, enhance, fostering, highlighting, showcasing, underscore.
  - Mid-2025–mid-2026: emphasizing, enhance, highlighting, showcasing.
  - Mid-2026 on: challenge, leverage, multifaceted, prioritize, quietly, universally, with 8–20-word sentences.
  - Grok: causal, empirical, correlate, underscore.
  - The page cautions that overuse of one word doesn't make its synonyms suspect. — [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- Copula avoidance ("serves as," "stands as," "boasts/features/offers" in place of is/are). Negative parallelisms: "Not just X, but also Y," "It's not…, it's…," "no…, no…, just…," and "Y rather than X". The page says the last of these is heavily used by recent LLMs. — [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- Rule of three (triads of adjectives or short phrases used to make shallow analysis look thorough). — [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- Style: title case in headings, overused bold, inline-header vertical lists, wrong heading levels, emoji at the start of headings or list items, curly quotes (“ ” ’). — [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- Chatbot leftovers: "I hope this helps," "Certainly!", "Would you like…", "let me know". Hedging disclaimers: "based on available information," "in the provided search results," "It's important to note". — [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- Placeholders: "[Article Title 1]", "2025-XX-XX", `INSERT_SOURCE_URL_30`, `PASTE_YOUTUBE_VIDEO_URL_HERE`. Markup: raw Markdown (`**`, `##`, `---`), and `contentReference[oaicite:1]`, which the page calls a strong, unambiguous tell. — [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- Citations:
  - `utm_source=chatgpt.com` / `utm_source=openai`, `utm_source=copilot.com`, `referrer=grok.com`. These prove a tool was used, not necessarily that the prose was generated.
  - Invalid ISBN checksums, DOIs that resolve to unrelated papers, books cited without page numbers, named references never used. — [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- Edit-summary tells: "adheres to Wikipedia guidelines," "preserved existing structure," "all claims verified." — [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- Moved to "historical indicators" (less reliable now): promotional language (2023–2025), knowledge-cutoff statements (2022–2023), section summaries, prompt refusals, em-dash overuse (listed as "2022–September 2026"), elegant variation. The section's body text was not retrieved; only its headings. — [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- Ineffective indicators: perfect grammar, formal prose, an isolated "Additionally," mixed registers, unsourced content. — [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- Caveats:
  - Don't rely solely on GPTZero or Pangram. They have non-trivial error rates and can be fooled by paraphrasing.
  - Human intuition fares no better. A 2025 study found humans at chance level. Expert annotators caught 90% of AI text but misflagged 3.3% of human text.
  - Human writing is drifting toward LLM style. — [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)

**Research: Kobak et al.**
- "Delving into LLM-assisted writing in biomedical publications through excess vocabulary". Authors: Kobak, González-Márquez, Horvát, Lause. Published in *Science Advances* 11(27), 2 Jul 2025.
  - Data: more than 15M PubMed abstracts, 2010–2024.
  - Method: the excess frequency of style words after ChatGPT appeared.
  - Result: "at least 13.5% of 2024 abstracts were processed with LLMs" (a lower bound), reaching 40% in some subcorpora (discipline, country, journal).
  - The authors say the effect exceeds that of Covid on vocabulary. — [arXiv 2406.07016](https://arxiv.org/abs/2406.07016)
- The specific excess words ("delves", "showcasing", "underscores") and their ratios were not visible on the abstract page, and the Science Advances page returned 403. [UNVERIFIED in this session; widely reported, see Gaps]

**Humanizer skill (local `~/.agents/skills/humanizer/SKILL.md`; upstream believed to be github.com/blader/humanizer [UNVERIFIED])**
- Encodes 33 patterns based on Wikipedia's page. Beyond Wikipedia it adds: elegant variation, false ranges, hyphenated word-pair overuse, persuasive authority tropes, signposting ("Let's dive in"), fragmented headers, manufactured punchlines and staccato drama, aphorism formulas, conversational rhetorical openers, generic positive conclusions, sycophantic tone. — local skill file
- Hard rule: the final rewrite must contain no em or en dashes ("one of the most reliable AI tells"), unless a user writing sample uses them. — local skill file
- Process:
  1. Identify the patterns.
  2. Draft a rewrite.
  3. Ask "What makes the below so obviously AI generated?" and "Does the rewrite state any fact… that isn't in the source?"
  4. Write the final rewrite.
  - Never invent facts. Calibrate to a voice sample when one exists. — local skill file
- False-positive guidance:
  - Don't flag perfect grammar, formal vocabulary, curly quotes alone (OSes auto-curl them), em dashes alone, one short emphatic sentence, or unsourced claims.
  - "Look for clusters of tells, not isolated ones."
  - Signs of human writing to preserve: specific, hard-to-fabricate detail, mixed feelings, era-bound references, varied sentence length, genuine asides, and text dated before 30 Nov 2022. — local skill file

### Inferences
- Wikipedia itself now dates its tells (em dash "2022–September 2026", promotional language "2023–2025"). Writing tells drift with each model generation, so lexical blacklists go stale. Structural patterns (negative parallelism, rule of three, -ing tails, copula avoidance) and verifiability problems (fake DOIs, placeholders) last longer.
- The two sources take different positions on em dashes. Humanizer bans them outright; Wikipedia files them as historical and warns against single-indicator judgments.

### Gaps
- The exact Kobak excess-word ratios (e.g., the multiplier for "delves") were not retrieved.
- The body text of Wikipedia's "Historical indicators" and "Style" sections was only partly read (the page is 250k characters).

## 3. Image tells and brand guidance

### Takeaway
Consumer guides converge on a short list of tells: malformed hands (extra fingers, missing thumbs), garbled or wavy text, over-smooth poreless skin, inconsistent eye reflections, shadows and lighting, and jewelry or tattoo artifacts. All of them warn these are fading as models improve. Brand-side guidance is mostly agency or vendor blog content. Its advice: avoid AI "office people / smiling customer" stock looks, specify exact hex values, and treat outputs as first drafts.

### Cited Findings
- Tells: a sixth finger, a missing thumb or extra joints; gibberish or wavy text; skin that is "too smooth", missing texture, asymmetry and stray hairs (this can be confused with retouching); mismatched eye reflections; lighting, shadow, jewelry and tattoo errors. — [Full Fact](https://fullfact.org/online/how-to-spot-ai-images/), [tech.co](https://tech.co/news/ways-detect-ai-images-examples), [Digital Camera World](https://www.digitalcameraworld.com/features/generative-or-genuine-my-5-surefire-ways-to-spot-an-ai-generated-image), [Android Authority](https://androidauthority.com/how-to-spot-ai-generated-images-3434166)
- These cues are "increasingly rare as models improve". Treat them as clues, not proof. — [PCWorld](https://www.pcworld.com/article/2505522/stop-being-tricked-by-ai-fakery-here-are-the-red-flags-to-look-for.html), [eWeek](https://www.eweek.com/news/5-simple-ways-spot-ai-generated-images/)
- Clutch says AI "office people" and "smiling customer" shots read as hollow and are judged poorly by consumers, and advises against AI imagery on product pages or where precision matters. — [Clutch](https://clutch.co/resources/brands-how-when-to-use-ai-imagery)
- Fixes from brand and agency blogs: give exact hex values, not "blue and orange"; treat every AI output as a first draft; keep a human in the loop. Their explanation is that brand guidelines are written for humans, so models fill the gaps with training defaults. — [Superside](https://www.superside.com/blog/why-ai-generated-creative-feels-off-brand), [Venngage](https://venngage.com/blog/ai-brand-consistency-guide/) (vendor bias: both sell AI tools)
- In UI work, the Refero skill bans "abstract blobs and generic 3D art", "weak CSS fakes for photos" and "stock imagery that could belong anywhere". Its fix: real photography, custom illustration, or an honest fixed-ratio placeholder. impeccable bans crude sketchy SVG scenes. — [refero](https://raw.githubusercontent.com/referodesign/refero_skill/f78b4eccf112d7a179b92afeafdd7e8684560ac2/references/anti-ai-slop.md), [impeccable](https://github.com/pbakaus/impeccable)
- iA argues "AI art is the new stock image". The essay was not read in full. — [iA](https://ia.net/topics/ai-art-is-the-new-stock-image)

### Inferences
- Aesthetic tells (glossy lighting, 3D clay/Pixar look, perfect symmetry, plastic sheen) appear widely in practitioner discussion. The sources retrieved here cover them only as "generic 3D art", "too smooth" and "stock look", so the more specific aesthetic list should be marked unverified.

### Gaps
- I found no formal, widely adopted brand-guideline clause that bans the "AI aesthetic"; it is a practice, not a standard.
- No primary source was retrieved for "3D clay/Pixar style" or "perfect symmetry" as named tells.

## 4. Social/marketing copy tells and platform stances

### Takeaway
On social platforms the reported tells are formulaic structure (generic opener, three lessons, manufactured vulnerability, neat triads), stock openers like "In today's fast-paced world", and a lack of personal specifics. Emoji-bullet counting is often discussed but poorly documented. Platforms mostly don't ban AI. They demote or demonetize "inauthentic", mass-produced, perspective-free content and label synthetic media.

### Cited Findings
- LinkedIn prevalence:
  - Originality.ai found 54% of long posts likely AI-assisted (Oct 2024). — [tech.co](https://tech.co/news/chatgpt-over-half-of-linkedin-posts-ai-generated)
  - Pangram, as cited by Fortune, found 41% of long-form posts fully AI-generated, Apr–Jun 2026. — [Fortune](https://fortune.com/2026/10/06/ai-slop-marketing-ghostwriter-copy/)
  - The two figures use different methods and definitions, so they are not directly comparable.
- Tell patterns:
  - "Clean intro, three lessons, fake vulnerability". The giveaway is missing personal detail. — [Product Hunt discussion](https://www.producthunt.com/p/imperfectly/what-is-the-fastest-way-you-can-tell-a-linkedin-post-was-ai-written)
  - Users analyze emojis and em dashes as AI signs; writers drop em dashes to avoid being flagged. — [Bloomberg](https://www.bloomberg.com/news/articles/2026-01-30/chatgpt-written-linkedin-posts-have-users-analyzing-emojis-other-ai-signs), [AOL](https://www.aol.com/articles/chatgpt-imbotster-syndrome-gumming-write-080801835.html)
  - The specific emoji patterns were not visible in the snippets.
- LinkedIn's own policy ("Keeping conversations real", Pressroom, 4 Jun 2026):
  - AI writing help is fine, but posts "need to represent your voice and your perspectives".
  - AI slop is defined as low-effort content that "can look polished but offers no unique perspective or substance".
  - Detection targets automated comments at scale and replies that merely restate the post.
  - Enforcement is reduced distribution beyond the poster's network, not bans. Initial testing identified generic content correctly 94% of the time. — [LinkedIn News](https://news.linkedin.com/2026/keeping-conversations-real-on-linkedin)
- YouTube:
  - YPP "repetitious content" was renamed "inauthentic content" (mass-produced or repetitive), effective 15 Jul 2025.
  - YouTube's examples: narrated stories with only superficial differences, and slideshows with the same narration.
  - YouTube (Rene Ritchie) described it as a clarification of an existing rule. Reaction and commentary channels are not targeted.
  - Coverage disagrees on whether existing monetized channels face removal. — [Search Engine Journal](https://searchenginejournal.com/youtube-targets-mass-produced-content-in-monetization-update/550337/), [Tubefilter](https://www.tubefilter.com/2025/07/03/youtube-crackdown-repetitive-non-original-content/amp/), [Social Media Today](https://www.socialmediatoday.com/news/youtube-clarifies-monetization-update-inauthentic-repeated-content/752892/)
  - The current help-center wording was not checked [UNVERIFIED].
- Meta:
  - Feb 2024: Meta announced it would label images from other companies' tools using industry signals (C2PA Content Credentials, IPTC, SynthID). — [TechCrunch](https://techcrunch.com/2024/02/06/meta-ai-generated-image-labelling/), [Meta](https://about.fb.com/news/2024/04/metas-approach-to-labeling-ai-generated-content-and-manipulated-media/)
  - The "Made with AI" label became "AI info" in Jul 2024, after photographers complained about false labels on real photos. — [PetaPixel](https://petapixel.com/2024/07/01/instagram-changes-made-with-ai-label-to-ai-info-after-widespread-backlash)
  - Sep 2024: the label for AI-edited content moved into the post menu, while fully generated content keeps a prominent label. — [TechCrunch](https://techcrunch.com/2024/09/12/meta-is-making-its-ai-info-label-less-visible-on-content-edited-or-modified-by-ai-tools), [Meta Transparency](https://transparency.meta.com/governance/tracking-impact/labeling-ai-content)
- Copy tells encoded in design skills: "Elevate", "Seamless", "Unleash", "Next-Gen", "Game-changer", "In the world of…", "Oops!", exclamation marks on success. — local redesign-skill. impeccable's detector also has `marketing-buzzword` and `theater-slop-phrase` rules (see section 5).

### Inferences
- The platforms converge on the same test. What gets penalized is the lack of a perspective, substance or originality, not AI use as such. That matches the "identity test" in the design skills.

### Gaps
- I found no primary source listing "In today's fast-paced world", emoji-bullet listicles or hook templates as named tells (they appear in community discussion only). TikTok and X policies were not researched.

## 5. Tools, skills and processes that encode these rules

### Takeaway
Three kinds of tools exist: (1) prompt or skill ban lists loaded into the generating model (Anthropic frontend-design, impeccable, taste/redesign/soft skills, Refero, humanizer); (2) deterministic linters that check CSS, DOM and text without an LLM (impeccable's detector); (3) statistical detectors (GPTZero, Pangram, Originality.ai) plus provenance metadata (C2PA, SynthID). The tools describe the same process in different words: set the context first, generate under the bans, detect (deterministically and with an LLM critique), classify, rewrite, then run a final "would someone say AI made this?" check.

### Cited Findings
- impeccable ships "46 deterministic detector rules plus LLM-only critique checks. The CLI and browser extension run the deterministic rules with no LLM and no API key" (`npx impeccable detect`). Hooks run the detector on UI file edits in Claude Code, Copilot and Codex, which surface findings after the edit; on Cursor the hook blocks bad writes before they land. — [impeccable README](https://github.com/pbakaus/impeccable)
- Detector rule IDs, read from the local copy of `scripts/detector`. They span UI, typography and copy, i.e. lint rules that are not limited to visual tells:
  - Color and surface: `ai-color-palette`, `cream-palette`, `gradient-text`, `dark-glow`, `gray-on-color`, `low-contrast`.
  - Borders, cards and shadows: `side-tab`, `border-accent-on-rounded`, `gpt-thin-border-wide-shadow`, `nested-cards`, `icon-tile-stack`.
  - Section scaffolding: `hero-eyebrow-chip`, `repeated-section-kickers`, `numbered-section-markers`.
  - Typography: `overused-font`, `single-font`, `flat-type-hierarchy`, `italic-serif-display`, `extreme-negative-tracking`, `wide-tracking`, `oversized-h1`, `tight-leading`, `tiny-text`, `all-caps-body`, `justified-text`, `line-length`.
  - Spacing and backgrounds: `monotonous-spacing`, `cramped-padding`, `repeating-stripes-gradient`, `codex-grid-background`.
  - Motion: `bounce-easing`, `layout-transition`, `image-hover-transform`.
  - Overflow and structure: `text-overflow`, `clipped-overflow-container`, `skipped-heading`.
  - Copy: `em-dash-overuse`, `marketing-buzzword`, `theater-slop-phrase`, `aphoristic-cadence`.
  - Design-system conformance: `design-system-color`, `design-system-font`, `design-system-radius`. — local `~/.claude/plugins/marketplaces/impeccable/.agents/skills/impeccable/scripts/detector/`
- impeccable's workflow commands include `init` (writes PRODUCT.md and DESIGN.md context), `shape` (plan before code), `craft`, `critique`, `audit`, `polish`, `distill`, `quieter`, `bolder` and `colorize`. The process is: build context, then shape, then build, then detect and critique, then refine. — [impeccable](https://github.com/pbakaus/impeccable)
- Anthropic's frontend-design skill is a roughly 400-token on-demand prompt. Its approach: name the defaults explicitly as things to avoid, then give positive direction (typography, theme, motion, background) and require a committed aesthetic. — [Claude blog](https://www.claude.com/blog/improving-frontend-design-through-skills)
- The redesign-skill works audit-first. It scans the existing UI against the checklist, then applies upgrades "without breaking functionality". taste-skill states the design direction first, asks at most one clarifying question, then runs a "strict pre-flight check". — local skill files
- The humanizer process is detect, then draft rewrite, then self-critique ("what makes this obviously AI?" plus a fact-invention check), then the final rewrite, with a deterministic scan for "—" and "–". — local skill file
- Text detectors (GPTZero, Pangram) have non-trivial error rates and can be evaded. Wikipedia does not accept a detector score alone as grounds for speedy deletion. — [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). LinkedIn reports 94% accuracy for its own internal classifier. — [LinkedIn](https://news.linkedin.com/2026/keeping-conversations-real-on-linkedin)
- Provenance tools Meta relies on: C2PA Content Credentials and Google SynthID watermarks. — [Meta](https://about.fb.com/news/2024/04/metas-approach-to-labeling-ai-generated-content-and-manipulated-media/)

### Inferences
- The tools that lean on deterministic, checkable rules (exact CSS properties, hex bands, OKLCH ranges, dash characters) can run as cheap, repeatable gates such as hooks or CI. Judgment checks (identity test, category reflex, "AI made that") still need a critique pass by an LLM or a human.
- All the ban lists carry dates or model-specific sections (Codex, Gemini). That suggests they should be maintained as living documents, and pairing each ban with a fix matters more than the ban itself.

### Gaps
- I did not verify the canonical GitHub URLs for taste-skill (leonxlnx) or humanizer (blader).
- The soft-skill, ui-ux-pro-max full rule sets and v0/Vercel guidance were not read in full.
- No independent evaluation of whether these skills measurably reduce "AI-looking" output was found.
