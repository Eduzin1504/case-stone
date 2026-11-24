# Design frameworks, processes and principles for distinctive (non-generic) work, and how they apply with AI in the loop

Verification note: sources marked **[fetched]** were read in full during this session. Sources marked **[search]** were seen only as search-result snippets or summaries. Sources marked **[canonical, not fetched]** are well-known official pages cited from background knowledge, and the report writer should spot-check them before quoting.

## 1. Double Diamond / Framework for Innovation, design thinking, divergence/convergence methods

### Takeaway
The process frameworks resist generic outcomes through structure. They require you to discover and reframe the problem before generating answers, they demand a wide divergent spread before converging, and they let teams loop back to earlier phases. Generative AI tends to skip the first diamond: it jumps straight to a plausible "Deliver" artifact for an unexamined problem. That is where sameness comes from.

### Cited Findings
- **Double Diamond, 4 phases** (Design Council, UK):
  - **Discover:** understand the problem rather than assume it, by speaking to and spending time with the people affected.
  - **Define:** use the discovery insight to frame the challenge in a different way.
  - **Develop:** generate different answers, seeking inspiration elsewhere and co-designing with a range of people.
  - **Deliver:** test solutions at small scale, reject those that won't work, improve those that will.
  — [Design Council, Framework for Innovation](https://www.designcouncil.org.uk/our-resources/framework-for-innovation/) [fetched]
- Each diamond is a divergent phase ("exploring an issue more widely or deeply") followed by a convergent one ("taking focused action"). The process is explicitly **non-linear**: what you learn during delivery can send you back, and early prototyping can count as discovery. — [Design Council](https://www.designcouncil.org.uk/our-resources/framework-for-innovation/) [fetched]
- **Framework for Innovation components:**
  - **Design principles:** "Put people first", "Communicate visually and inclusively", "Collaborate and co-create", "Iterate, iterate, iterate".
  - **Methods bank:** grouped as Explore (challenges, needs, opportunities), Shape (prototypes, insights, visions) and Build (ideas, plans, expertise).
  - **Engagement:** "Developing connections and building relationships is as important as creating ideas".
  - **Leadership:** permission to experiment and change course.
  — [Design Council](https://www.designcouncil.org.uk/our-resources/framework-for-innovation/) [fetched]. The current page does not state the 2019 date. It is commonly reported as the 2019 update, but I could not confirm that on the page.
- **How Might We (HMW):** IDEO's Field Guide tells teams to recast insight statements as HMW questions, framing a solution as possible. — [IDEO Field Guide PDF](https://unosd.un.org/sites/unosd.un.org/files/ideo_field_guide_to_human-centered_design.pdf); [IDEO Design Kit methods](https://www.designkit.org/methods.html) [search]
- The d.school frames HMWs as a way to turn a point of view into actionable provocations. Its suggested moves include amplifying the good, removing the bad, exploring the opposite, questioning an assumption, and pushing an idea to an extreme. — [d.school, How Might We Questions](https://dschool.stanford.edu/tools/how-might-we-questions) [search]
- NN/g traces the HMW template to Procter & Gamble in the 1970s, later adopted by IDEO. — [NN/g, How Might We Questions](https://www.nngroup.com/articles/how-might-we-questions/) [search]
- **Crazy 8s:** fold a sheet into 8 panels, set a 60-second timer per panel, sketch 8 distinct variations in 8 minutes, fast and messy, kept private at first. It comes from the GV Design Sprint (Jake Knapp), where it sits in the Sketch step. The sprint is commonly described as Understand/Map, Sketch, Decide, Prototype, Test. Labels vary by source. — [Clearleft, Crazy Eights](https://clearleft.com/posts/crazy-eights); [Open Practice Library](https://openpracticelibrary.com/practice/crazy-8s/) [search]
- **Morphological analysis / Zwicky box:** the search returned no usable source. See Gaps.

### Inferences
- The anti-generic lever in these frameworks is the **reframe in "Define"**. A distinctive output usually follows from a distinctive problem framing. AI prompted with a category ("a landing page for a fintech") skips Discover and Define entirely and returns the category mean.
- Crazy 8s works because it forces you past the first 2–3 obvious ideas. Panels 5–8 are where non-obvious ideas show up. The AI analogue is to ask for many variants and then deliberately throw away the first few, the most "probable" ones.
- HMW provocations ("explore the opposite", "push to an extreme") are prompt-ready divergence operators. They map directly onto instructions you can give a model.

### Gaps
- No primary source fetched for the d.school "Bootleg" mode list (Empathize, Define, Ideate, Prototype, Test) or for IDEO's Inspiration/Ideation/Implementation framing.
- No primary source found for morphological analysis (Fritz Zwicky). The method itself is well established: list a problem's independent parameters, list options per parameter, combine across the matrix. I could not cite it this session.
- I could not confirm the 2019 date of the Framework for Innovation on the current Design Council page.

## 2. Brand strategy and identity processes (agencies, Neumeier, Wheeler)

### Takeaway
Agency identity work treats strategy as a mandatory gate before any visual output. Research, then a positioning or "onliness" claim, then design. Distinctiveness is defined as provable difference from competitors, not as aesthetic novelty. Agency leaders (Collins) say openly that using AI to "generate everything" destroys the originality that gives a brand its value.

### Cited Findings
- **Wheeler, *Designing Brand Identity*, 5 phases:**
  1. Conducting Research
  2. Clarifying Strategy
  3. Designing Identity (symbols, logotype and signature, color, typography, sound, motion, trial applications, presentation)
  4. Creating Touchpoints
  5. Managing Assets
  — [Table of contents, uni.li](https://toc.uni.li/FLMF039378.pdf); [AIGA Raleigh recap](https://raleigh.aiga.org/?p=11474) [search]
- An event recap says each phase has specific tasks to complete before moving to the next. — [AIGA Raleigh recap](https://raleigh.aiga.org/?p=11474) [search]
- Wheeler says the process exists to "build confidence in the solution, confidence in the people… and also to just reduce what I call brand anxiety." — [Logo Geek podcast 10](https://logogeek.uk/podcast10) [search]
- **Neumeier, *Zag*:** in cluttered markets, ordinary differentiation isn't enough. You need "radical differentiation", which he calls the "zag". — [Mark Ramsey Media interview](https://www.markramseymedia.com/amp/your-radio-station-needs-to-zag-an-interview-with-author-marty-neumeier) [search]
- **Onliness statement:** "Our [brand] is the only ___ that ___." If you can't fill it with "only", you don't have a zag. The statement then drives decisions about features, communications and resources. — [Zag, O'Reilly ch. 19 "What makes you the only?"](https://www.oreilly.com/library/view/zag-the-number-one/0321426770/ch19.html); [Adweek, "And You Swore 'Onliness' Wasn't a Word"](https://www.adweek.com/?p=677058) [search]
- *Zag* is reported to contain a 17-step process. That claim comes only from a Blinkist summary, so the count is unverified. — [Blinkist](https://www.blinkist.com/books/zag-en) [search]
- **Collins:** its offering runs in sequence: brand strategy and naming, then identity systems and verbal branding, then messaging, then governance. — [Collins, About](https://wearecollins.com/about) [search]
- Brian Collins on AI:
  - Collins has "been working with AI for years".
  - Companies that use AI "to generate everything" may "lose the very thing that makes their brand valuable: originality."
  - Creativity is "a process of discovery". Writing is "how you figure out what you actually think".
  - "AI doesn't think." He calls it "alien intelligence".
  - Use it to "enhance creativity instead of erasing it".
  — [Transform magazine, "The scoop with Collins" (2025)](https://www.transformmagazine.net/articles/2025/the-scoop-with-collins/) [fetched]
- **Pentagram, identity derived from the subject's own material:**
  - Frist Art Museum: the stylized "S" is based on a marking on a tile in the 1930s building. — [Dezeen](https://www.dezeen.com/2018/07/13/pentagram-rebrands-frist-art-museum-nashville-tennessee-1930s-art-deco-logo/) [search]
  - Baltimore Center Stage: the logo was inspired by performers' stage tape marks and evokes marquee signage. — [Pentagram](https://www.pentagram.com/work/baltimore-center-stage) [search]
  - Studio Theatre: type references the building's industrial past. — [Pentagram](https://www.pentagram.com/work/studio-theatre/story) [search]

### Inferences
- The Pentagram examples show a repeatable move: **mine the client's own artifacts** (building, tools of the trade, history) for the formal idea. Because no other client has those artifacts, the result can't be the category average. With AI in the loop, this means feeding real photographed or collected source material in as references, not adjectives.
- An onliness statement is a test you can run on AI output: if a competitor could also claim the identity, it fails.
- Wheeler's gated phases are the opposite of the "prompt → finished logo" workflow. Phases 1–2 produce the brief that makes Phase 3 non-generic.

### Gaps
- No Wolff Olins or Koto process write-ups were found or fetched this session.
- No detail was found on the sub-steps of Wheeler's Phases 1–2 beyond the phase titles. Catalog listings mention a brand brief, creative brief and naming, but those were not verified.

## 3. Design principles: Rams, Gestalt, Nielsen, Refactoring UI (restraint and hierarchy)

### Takeaway
These principles push toward restraint: fewer elements, a clear hierarchy, nothing decorative without a function. NN/g's AI testing found that AI tools do the reverse. They "often generate more elements than a task needs", so the principles serve best as an editing and review pass over AI output.

### Cited Findings
- **Dieter Rams, 10 principles of good design.** Good design is: innovative, makes a product useful, aesthetic, makes a product understandable, unobtrusive, honest, long-lasting, thorough down to the last detail, environmentally friendly, and "as little design as possible" ("Less, but better"). — [Vitsœ, Good design](https://www.vitsoe.com/us/about/good-design) [canonical, not fetched]
- **Nielsen heuristic #8, "Aesthetic and minimalist design":** interfaces should not contain irrelevant or rarely needed information, because every extra unit competes with the relevant units and lowers their relative visibility. — [NN/g, 10 Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/) [canonical, not fetched]
- **Gestalt principles** (proximity, similarity, common region, continuity, closure, figure/ground) describe how people group elements. Spacing and alignment communicate structure before any decoration does. — [NN/g, Gestalt proximity](https://www.nngroup.com/articles/gestalt-proximity/) [canonical, not fetched]
- **Refactoring UI (Wathan & Schoger):**
  - Build hierarchy with weight, color and contrast rather than size alone. De-emphasize secondary content instead of emphasizing everything.
  - Start with too much whitespace and remove it.
  - Use constrained, pre-defined scales for spacing, type and color instead of arbitrary values.
  - Don't rely on borders or boxes to separate content.
  — [refactoringui.com](https://www.refactoringui.com/) [canonical, not fetched]
- **NN/g on AI prototyping (Oct 24, 2025):**
  - Tools "often generate more elements than a task needs".
  - Output must be manually checked for hierarchy, grouping, contrast and spacing.
  — [NN/g, "Good from Afar, But Far from Good: AI Prototyping in Real Design Contexts"](https://www.nngroup.com/articles/ai-prototyping/) [fetched]

### Inferences
- Rams' "as little design as possible" and Nielsen #8 work as **subtraction passes**: for each element, ask what function it serves and delete it if none. AI output, padded with extra cards, badges, gradients and icons, typically fails this test.
- There is a nuance here. Restraint is not the same as generic. The current AI default (sans-serif, minimal, rounded cards) is "minimal-looking" without being *restrained by intent*. These principles demand that every element be justified by the content, which is a different thing from looking sparse.

### Gaps
- Rams, Nielsen, Gestalt and Refactoring UI were not fetched this session. Wording above is paraphrased from background knowledge and should be spot-checked against the cited canonical pages.

## 4. Design critique methods

### Takeaway
Structured critique judges work against stated objectives, not personal taste. This makes it the right instrument for evaluating AI output: it asks "does this element serve the goal?", not "does this look nice?". Polished-but-generic output easily passes the second question and fails the first.

### Cited Findings
- **Connor & Irizarry, *Discussing Design* (O'Reilly, 2015):**
  - Critique has a recipient, who acts on it, and givers, who analyze the design.
  - Clarity of **intent** "is often what separates successful critiques… from problematic ones".
  — [O'Reilly, ch. 2](https://www.oreilly.com/library/view/discussing-design/9781491902394/ch02.html) [search]
- The book distinguishes three kinds of feedback:
  - **direction:** "do X"
  - **reaction:** gut response
  - **critique:** analysis of whether specific elements are effective in achieving the product's objectives
  — [O'Reilly, Discussing Design](https://www.oreilly.com/library/view/discussing-design/9781491902394/) [search]
- The commonly taught critique question structure from the book: What is the objective? What elements relate to it? Are they effective? Why or why not? This is my paraphrase of the book's framing. — [O'Reilly, ch. 2](https://www.oreilly.com/library/view/discussing-design/9781491902394/ch02.html) [search]
- Unfacilitated critiques fragment because each participant applies their own criteria. A facilitator keeps everyone on agreed objectives. — [O'Reilly, Discussing Design](https://www.oreilly.com/library/view/discussing-design/9781491902394/) [search]

### Inferences
- An AI-assisted workflow can use the critique format as a rubric. State the objectives and the brief, then for each element ask whether it is effective toward a stated objective. Add a distinctiveness question: "could this appear unchanged for a competitor?"
- "Reaction" feedback ("looks clean/modern") is exactly what generic AI output is optimized to win. Critique structure moves the conversation off that axis.

### Gaps
- No primary source fetched for other crit formats (art-school crits, Pixar "Braintrust", design review rubrics at specific companies).

## 5. Designing from constraints, the subject's vernacular, research, mood boards and briefs

### Takeaway
The best-documented antidote to sameness, in both pre-AI agency practice and NN/g's AI research, is **specific inputs**: real references, real subject material, named styles and a concrete brief. Without them, AI tools "fill gaps with assumptions" drawn from the most common patterns. Ground the work in the subject's own vernacular (its buildings, tools, signage, history) and do the core design thinking before the tool is opened.

### Cited Findings
- NN/g (Oct 2025):
  - Without visual style specs, tools output "a similar, generic look" (sans-serif, minimal styling) and default to libraries like shadcn and Tailwind CSS.
  - Many screens look "flat and interchangeable".
  - Vague prompts force tools to "fill gaps with assumptions". "Profile" was read as a social-media profile.
  — [NN/g, AI Prototyping](https://www.nngroup.com/articles/ai-prototyping/) [fetched]
- NN/g recommendations:
  - Name the visual style, design language, components and states.
  - **Attach references** (sketches, mockups, **moodboards**, Figma frames). Higher-fidelity references gave more accurate results.
  - Disambiguate UX terms.
  - Use long, detailed prompts once a direction exists, and save broad prompts for early exploration.
  - Refine manually.
  - Do the core design thinking first, since "much of the design work often happens before the AI tool is involved".
  — [NN/g, AI Prototyping](https://www.nngroup.com/articles/ai-prototyping/) [fetched]
- NN/g advises naming established design styles or frameworks instead of vague terms like "clean and modern". — [NN/g, AI design tools update 2](https://www.nngroup.com/articles/ai-design-tools-update-2/) [search]
- NN/g's "vague prototyping" article argues that deliberately vague prompts are useful early for divergent exploration. — [NN/g, Vague Prototyping](https://www.nngroup.com/articles/vague-prototyping/) [search]
- Vernacular and subject-grounded identity examples: Pentagram's Frist (a building tile mark), Baltimore Center Stage (stage tape marks, marquees) and Studio Theatre (industrial past). — [Dezeen](https://www.dezeen.com/2018/07/13/pentagram-rebrands-frist-art-museum-nashville-tennessee-1930s-art-deco-logo/); [Pentagram BCS](https://www.pentagram.com/work/baltimore-center-stage); [Pentagram Studio Theatre](https://www.pentagram.com/work/studio-theatre/story) [search]

### Inferences
- A workable AI-era sequence:
  1. Research and collect primary references from the subject itself (photos, artifacts, documents, local typography).
  2. Write a brief with an onliness claim and explicit constraints.
  3. Run divergent generation with broad or provocation prompts (HMW operators, Crazy-8s-style "8 distinct variants, discard the obvious").
  4. Converge with specific prompts plus attached references.
  5. Critique against objectives and the distinctiveness test.
  6. Do a subtraction pass (Rams, Nielsen #8, Refactoring UI hierarchy).
- Constraints work as anti-averaging devices. A real constraint (a material, a building, a client's archive) pulls output away from the training-data mean, while adjectives ("modern, bold") pull toward it.

### Gaps
- I did not find a primary source on "vernacular design" as a named method (for example, Robert Venturi's *Learning from Las Vegas*, or writing on vernacular typography). Nor did I find a fetched source on brief-writing templates.

## 6. What design leaders published 2023–2026 about avoiding AI sameness

### Takeaway
There is broad consensus in 2025–2026 writing on several points:
- AI accelerates a convergence that predates it. Commentators point to an already flattened, template-driven aesthetic.
- The visible AI defaults are identifiable: generic sans-serif type, rounded cards, gradient heroes, purple-on-white, shadcn/Tailwind look.
- The remedy is human judgment, taste exercised through hands-on craft, and specific inputs. Better models alone don't fix it.

### Cited Findings
- **Creative Bloq, Vanessa Porter, "Everything looks the same. Now what?" (6 June 2026):** design was already converging on "a single aesthetic before AI arrived", and AI accelerates it. The example is cybersecurity sites: dark navy, electric blue, shields and padlocks, abstract network diagrams. The fetched excerpt was truncated, so its recommendations were not captured. — [Creative Bloq](https://www.creativebloq.com/ai/everything-looks-the-same-now-what) [fetched, partial]
- **Fast Company, "AI isn't design's biggest problem":** graphic design was already standardized before AI. — [Fast Company](https://www.fastcompany.com/91382025/ai-isnt-designs-biggest-problem) [search]
- **Built In, "AI Makes Bad Design Look Good Enough" (June 2026):** AI product interfaces are generic and interchangeable ("AI design slop"). — [Built In](https://builtin.com/articles/ai-design-slop-era) [search]
- **NN/g (2024–2025):**
  - AI design tools were "not ready" in 2024. The work needed for high-quality results was too time-consuming.
  - A May 2025 update found improved usefulness, with designers "not in danger of being replaced".
  - The most-adopted tools are narrow in scope.
  — [NN/g, AI design tools not ready](https://www.nngroup.com/articles/ai-design-tools-not-ready/); [NN/g, update 2](https://www.nngroup.com/articles/ai-design-tools-update-2/) [search]
- **NN/g:** AI prototyping tools "lack the intuition to tailor them to nuanced contexts, even when provided with detailed instructions". Use them to explore, not as a final product. — [NN/g video, AI-Assisted Prototyping](https://www.nngroup.com/videos/ai-assisted-prototyping/) [search]
- **Figma (Config 2025 coverage):** sessions shifted from speed toward how to stand out when everything looks alike, and framed AI as augmenting craft. — [Figma blog, "Double click: Does efficiency kill love?"](https://www.figma.com/blog/double-click-does-efficiency-kill-love/) [search]
- **Figma (Config India recap):** a designer says there is too much of the same thing and designers need to protect their aesthetic. — [Figma blog](https://www.figma.com/blog/making-something-human-4-things-we-took-away-from-config-india/) [search]
- **Loredana Crisan (Figma CDO):** taste comes largely from hands-on work, because ideas surface only once you dig into a problem. — [It's Nice That](https://www.itsnicethat.com/features/in-house-figma-loredana-crisan-creative-industry-080726) [search]
- **Beyond (agency), on Config 2026:** taste is widely shared, but craft (applying taste under real constraints) is the scarce skill. — [Beyond](https://www.bynd.com/articles/raise-the-ceiling-beyonds-takeaway-from-figma-config-2026) [search]
- **Forrester on Config 2025:** "In an AI world, design matters more than ever." — [Forrester](https://www.forrester.com/blogs/figma-config-2025-in-an-ai-world-design-matters-more-than-ever) [search]
- **UX Collective, "AI design isn't ugly, it's fluent, and that's the problem":** the same look appears across tools. The piece cites Anthropic's own design criteria naming "purple gradients over white cards" as a telltale AI failure. — [UX Collective](https://uxdesign.cc/ai-design-isnt-ugly-it-s-fluent-and-that-s-the-problem-131b2f4eb78c) [search; secondary, verify]
- **Brian Collins (2025):** using AI "to generate everything" risks losing "originality". — [Transform](https://www.transformmagazine.net/articles/2025/the-scoop-with-collins/) [fetched]
- **Research context, via secondary sources only:**
  - A Wharton study (reported as *Nature Human Behaviour*, 2025) found ChatGPT-assisted brainstorming reduced idea variety across participants.
  - "Artificial Hivemind" (NeurIPS 2025) found different models give very similar outputs.
  — [HackerNoon](https://hackernoon.com/why-ai-is-making-everything-look-and-sound-the-same) [search; secondary, verify originals]
- **Duke Pratt:** commercial LLM creative outputs are more similar to each other than users might hope. — [Duke Pratt](https://pratt.duke.edu/news/ai-vs-human-creativity/) [search]

### Inferences
- The practitioner consensus lines up with the process literature. Sameness comes from skipping research and framing, from vague inputs, and from evaluating by "reaction" rather than critique against objectives. The fix is procedural, not stylistic. Banning specific AI tells (purple gradients) treats a symptom, and models will converge on the next default.
- Because sameness predates AI (Creative Bloq, Fast Company), a "not AI-looking" goal is not the same as a "distinctive" goal. Distinctiveness has to be anchored in the subject (onliness, vernacular, references), not defined against AI defaults.

### Gaps
- No full transcript was found of a specific Config talk on "sameness". Coverage comes from Figma blog recaps and attendee posts.
- I did not find a specific essay titled "the great flattening" in the design context.
- I did not fetch the original Wharton and NeurIPS papers. Treat those claims as secondary until verified.
- I could not find an NN/g article specifically on "AI design sameness" as a named topic. The relevant NN/g material is in its AI prototyping and tool-evaluation articles above.
