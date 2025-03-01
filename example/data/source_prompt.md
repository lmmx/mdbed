I want to write a preparatory note (which might go in a blog series)

A working title is: "Notes towards better maps of codebase territories"

It doesn't really roll off the tongue but I want to start things off.

So I have some notes on my whiteboard and I want to get these down before I move on.

The jottings I have are bullets with arrows swooping down into subpoints

- explosive number of ways to partition docs
-> motivates **opinionated** model of docs

- Stable references during refactors
-> motivates high-level (module/member) approach with **spanning trees** over the rest
-> motivates docs systems linked / linked with code that suggest **global** namespace of objects in invetory if not found
     -> like inline snapshot

- Docs is a snapshot of state (form) like snapshot tests are s.s. of state (behaviour)

The notes section ends there and in another colour I wrote:

CAS (Content Addressable Storage)
CA (Content Addressing)

Bergson's pre-image setting in : Doors
+
Bergson: pre-image stimuli : Windows ON

<- Motions ->
Ability to steer moving

(that part is not super clear to me what it means but it sort of talks about a "doors and windows: on, motions: on" [the announcement you get from an in-vehicle system] as a style of preparing to perform cybernetic work, cybernetes being from the word to steer -- it's a bit of a poetic jotting unlike the earlier more abstract but clearly technical writing notes

---

then there are 3 points:

1) fulfil all docstring requirements
2) fill out standard readme
3) autogen docs

that bit is self-contained, but in the same colour pen as the following:

so the following bit is quite specific, it comes from a sort of systematising of the aspects of a mkdocstrings docs system, let me show you it first then i'll help explain

---

<u>Territory<u>
Source tree

then to the right of that

<u>Map</u>
mkdocstrings modules/classes - members
(+options flags)

<u>UI</u>
nav:

---

so what is being done here is trying to connect back to the earlier concept of map vs territory, saying quite clearly "territory = source tree" (we would just say really that we are talking about what the recent MutaGReP paper calls "repository-grounding", I just didn't use the same terminology). now that I have read the MutaGReP paper I have the language to talk about this, so it's really important that I get this idea out clearly. The next thing it says under the title "Map" is about the idea that we want to make a map of the source tree terrirory, and we use mkdocstrings to keep this in the source tree and we sort of structure the it as a layer over the territory, basically a data model with entities of modules classes (the "members" field you specify in mkdocs syntax using `::` replacing the need for RST). you also set options flags, and this together constitutes the map. but then I recalled that this is not in itself the UI that the website viewer sees, there is also another level in the nav (but this lives in the central mkdocs.yml). I suspect that you could use Bergon's pre-image / image (as in his systematisation of memory as pure memory, an unextended virtual past vs. memory-images, the selective representational forms into which pure memory is contracted when consciousness actively recalls it to inform present action) in conjunction with this systematisation of what i called content addressing / content-addressable storage (by this I was making an analogy to git's CAS in which for instance file content  is addressable thus hashed and therefore moves without content modification are detected as renames, and by analogy/extension you would say that were the content to be the grounded intents of the symbols [though I didnt use this terminology at the time] then you would achieve quite naturally the outcome where moving *semantic* content without modification - i.e. what we routinely call "a refactor" - would be possible *even with modification to the content* i.e. we would achieve a way to detect code with equivalent purpose or outcomes, which is a long-standing goal in program synthesis research, to be able to tell if two ASTs are equivalent in outcome even if differing in syntax etc, such as a listcomp vs a for loop).