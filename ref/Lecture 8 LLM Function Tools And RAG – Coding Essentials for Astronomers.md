---
created: 2025-11-07T13:05:19 (UTC -05:00)
tags: []
source: https://tingyuansen.github.io/coding_essential_for_astronomers/lectures/lecture08-llm-function-tools-and-rag.html
author: 
---

# Lecture 8: LLM Function Tools And RAG – Coding Essentials for Astronomers

> ## Excerpt
> Last lecture, you mastered the art of programmatic conversation with Claude. You learned to extract structured data from observation logs, analyze astronomical images, and build conversation systems that maintain context. But if you're like most students after Lecture 7, you probably noticed something: Claude was helpful at understanding and explaining astronomical concepts, but when it came to actual calculations, you were still doing all the mathematical work yourself.

---
## Introduction

Last lecture, you mastered the art of programmatic conversation with Claude. You learned to extract structured data from observation logs, analyze astronomical images, and build conversation systems that maintain context. But if you're like most students after Lecture 7, you probably noticed something: Claude was helpful at understanding and explaining astronomical concepts, but when it came to actual calculations, you were still doing all the mathematical work yourself.

Today, that changes. You're about to cross the threshold from having an AI that talks about astronomy to having an AI that does astronomy. By the end of this lecture, you'll command an AI assistant that can calculate stellar parallaxes, determine orbital periods, analyze light curves, and search through your entire course knowledge base—all while you focus on the science rather than the implementation details.

Consider this scenario: You're analyzing a dataset of binary star observations for your research project. You have radial velocity measurements over time, and you need to determine the orbital period and calculate the system's total mass. In the pre-function-tools world, this meant hours of looking up formulas, writing NumPy code, debugging array operations, and manually searching through lecture notes for the relevant theory.

In the post-function-tools world, you simply say: "Analyze this binary star dataset—determine the orbital period and calculate the total mass." Claude automatically calls your period-finding function with the radial velocity data, executes mass calculations using Kepler's laws, and returns a complete analysis with both computational results and theoretical context.

This isn't about replacing your astronomical knowledge—it's about amplifying it. Every function Claude calls uses physics you understand. Every calculation builds on mathematical concepts you've learned. But now these capabilities operate at machine speed and scale.

### Why Function Tools Transform Your Research

The transformation we're making today fundamentally shifts how you interact with computation. Instead of an assistant that knows things, you get an assistant that can do things.

**Claude as Information Source (Lecture 7):**

-   You: "What's the formula for stellar luminosity?"
-   Claude: "Here's the Stefan-Boltzmann law: L = 4πR²σT⁴"
-   You: Spend 20 minutes implementing this in NumPy, debugging array shapes

**Claude as Computational Partner (Today):**

-   You: "Calculate the luminosity of this star given its radius and temperature"
-   Claude: Directly calls your `stellar_luminosity()` function with the parameters
-   Claude: Returns the calculated result immediately, plus physical interpretation

But here's what matters: you're not becoming less capable—you're becoming more powerful. Every function Claude calls is one you understand and could write yourself (using skills from Lectures 1-6). Every calculation follows physics principles you've learned. Claude handles the mechanical execution; you provide the scientific direction, validation, and creative thinking.

This workflow mirrors how professional astronomy works. Research astronomers don't rewrite basic calculations from scratch for every project. They build libraries of tested functions and focus their mental energy on novel scientific questions. Today, you start building those libraries and learning to orchestrate them through AI collaboration.

Function tools represent a fundamental shift in how LLMs interact with your code. Until now, when you asked Claude to calculate something, it would describe the calculation process in text. You then had to implement that calculation yourself in Python. Function tools eliminate this middle step—Claude can now directly execute Python functions you've written.

Think of it like the difference between having an assistant who can only read instruction manuals versus one who can actually operate the equipment. The first can tell you how to use a telescope; the second can actually point it at the stars and take measurements.

Here's the key concept: you write Python functions using all the skills you've learned—NumPy arrays from Lecture 4, matplotlib plots from Lecture 6, file operations from Lecture 3. Then you describe these functions to Claude in a special format called a "function schema." Once Claude knows about your functions, it can call them directly when answering questions.

**The Function Tool Workflow:**

1.  **You define**: Write a Python function using familiar tools (just like Lecture 5)
2.  **You describe**: Create a schema that tells Claude what the function does
3.  **User asks**: Someone poses a question requiring calculation
4.  **Claude decides**: Whether to use a function based on the question
5.  **Claude requests**: Tells you which function to run with what parameters
6.  **You execute**: Run the function and send results back
7.  **Claude interprets**: Incorporates the results into a natural language response

When someone asks "What's the distance to a star with 0.05 arcsecond parallax?", Claude recognizes this requires calculation, requests your distance function with the parameter 0.05, and then explains the result in astronomical context.

### The Schema Concept

A function schema is like a user manual for your function—it tells Claude what the function does, what parameters it needs, and when to use it. Without a schema, Claude wouldn't know your function exists or how to use it.

Think of schemas as the bridge between natural language and code. When someone asks "What's the distance to Alpha Centauri if its parallax is 0.75 arcseconds?", the schema helps Claude understand:

-   This question needs the `parallax_to_distance` function
-   The function needs one parameter: `parallax_arcsec`
-   The value for that parameter is 0.75

The schema format might look complex at first, but it's just a structured way to describe what you'd tell a colleague about your function: what it does, what inputs it needs, and what outputs it provides.

Let's create your first function tool step by step. We'll start with the simplest possible astronomical calculation and gradually build complexity.

### Setting Up the Environment

First, let's import what we need. Everything here should be familiar from previous lectures:

```
<span></span><span># Standard imports from previous lectures</span>
<span>import</span><span> </span><span>numpy</span><span> </span><span>as</span><span> </span><span>np</span>  <span># For mathematical operations (Lecture 4)</span>
<span>import</span><span> </span><span>os</span>          <span># For environment variables (Lecture 3)</span>
<span>from</span><span> </span><span>dotenv</span><span> </span><span>import</span> <span>load_dotenv</span>  <span># For loading API keys (Lecture 7)</span>
<span>import</span><span> </span><span>anthropic</span>   <span># For talking to Claude (Lecture 7)</span>

<span># Load API key from .env file (same as Lecture 7)</span>
<span>load_dotenv</span><span>()</span>
<span>client</span> <span>=</span> <span>anthropic</span><span>.</span><span>Anthropic</span><span>(</span><span>api_key</span><span>=</span><span>os</span><span>.</span><span>getenv</span><span>(</span><span>'ANTHROPIC_API_KEY'</span><span>))</span>

<span>print</span><span>(</span><span>"✓ Environment ready for function tools"</span><span>)</span>
```

```
✓ Environment ready for function tools
```

### Creating a Simple Astronomical Function

Let's start with the most fundamental calculation in stellar astronomy: converting parallax to distance. The parallax of a star is the tiny angle it appears to shift when viewed from opposite sides of Earth's orbit. The smaller this angle, the farther away the star.

The relationship is beautifully simple: distance (in parsecs) = 1 / parallax (in arcseconds). One parsec is the distance at which a star would have a parallax of exactly one arcsecond.

```
<span></span><span>def</span><span> </span><span>parallax_to_distance</span><span>(</span><span>parallax_arcsec</span><span>):</span>
<span>    </span><span>"""</span>
<span>    Convert stellar parallax to distance in parsecs.</span>
<span>    </span>
<span>    The fundamental equation: d = 1/p</span>
<span>    where d is distance in parsecs and p is parallax in arcseconds.</span>
<span>    """</span>
    <span># Input validation - always check for invalid inputs!</span>
    <span>if</span> <span>parallax_arcsec</span> <span>&lt;=</span> <span>0</span><span>:</span>
        <span>return</span> <span>{</span><span>"error"</span><span>:</span> <span>"Parallax must be positive"</span><span>}</span>
    
    <span># Calculate distance using the parallax formula</span>
    <span>distance_pc</span> <span>=</span> <span>1.0</span> <span>/</span> <span>parallax_arcsec</span>
    
    <span># Return as a dictionary for structured data</span>
    <span># We round to 2 decimal places for readability</span>
    <span>return</span> <span>{</span><span>"distance_parsecs"</span><span>:</span> <span>round</span><span>(</span><span>distance_pc</span><span>,</span> <span>2</span><span>)}</span>
```

Let's test our function manually to make sure it works correctly. We'll use Proxima Centauri, our nearest stellar neighbor:

```
<span></span><span># Test with Proxima Centauri's parallax (0.768 arcsec)</span>
<span>test_result</span> <span>=</span> <span>parallax_to_distance</span><span>(</span><span>0.768</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"Distance to Proxima Centauri: </span><span>{</span><span>test_result</span><span>[</span><span>'distance_parsecs'</span><span>]</span><span>}</span><span> parsecs"</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"That's about </span><span>{</span><span>test_result</span><span>[</span><span>'distance_parsecs'</span><span>]</span><span> </span><span>*</span><span> </span><span>3.26</span><span>}</span><span> light-years"</span><span>)</span>

<span># Test error handling with invalid input</span>
<span>error_test</span> <span>=</span> <span>parallax_to_distance</span><span>(</span><span>-</span><span>1</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"</span><span>\n</span><span>Error handling test: </span><span>{</span><span>error_test</span><span>}</span><span>"</span><span>)</span>
```

```
Distance to Proxima Centauri: 1.3 parsecs
That's about 4.2379999999999995 light-years

Error handling test: {'error': 'Parallax must be positive'}
```

### Defining the Function Schema

Now we need to tell Claude about our function. A schema describes three key things:

1.  **The function's name** - what Claude will call it
2.  **What it does** - helps Claude know when to use it
3.  **What inputs it needs** - the parameters and their types

The schema uses a specific format that might look intimidating at first, but it's just a nested dictionary structure (from Lecture 2). Let's build it step by step:

```
<span></span><span># Create a tools list with our function schema</span>
<span>tools</span> <span>=</span> <span>[</span>
    <span>{</span>
        <span>"name"</span><span>:</span> <span>"parallax_to_distance"</span><span>,</span>  <span># The exact function name</span>
        <span>"description"</span><span>:</span> <span>"Calculate stellar distance from parallax measurement in arcseconds"</span><span>,</span>
        <span>"input_schema"</span><span>:</span> <span>{</span>  <span># Describes what inputs the function needs</span>
            <span>"type"</span><span>:</span> <span>"object"</span><span>,</span>  <span># The inputs are structured as an object</span>
            <span>"properties"</span><span>:</span> <span>{</span>  <span># List of parameters</span>
                <span>"parallax_arcsec"</span><span>:</span> <span>{</span>  <span># Parameter name (must match function)</span>
                    <span>"type"</span><span>:</span> <span>"number"</span><span>,</span>  <span># This parameter is a number</span>
                    <span>"description"</span><span>:</span> <span>"Parallax angle in arcseconds (must be positive)"</span>
                <span>}</span>
            <span>},</span>
            <span>"required"</span><span>:</span> <span>[</span><span>"parallax_arcsec"</span><span>]</span>  <span># This parameter is mandatory</span>
        <span>}</span>
    <span>}</span>
<span>]</span>

<span>print</span><span>(</span><span>"✓ Function schema defined"</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"Claude now knows about </span><span>{</span><span>len</span><span>(</span><span>tools</span><span>)</span><span>}</span><span> function(s)"</span><span>)</span>
```

```
✓ Function schema defined
Claude now knows about 1 function(s)
```

### Making Your First Function Tool Call

Now for the exciting part—let's ask Claude a question and see if it recognizes that it needs to use our function. This is different from Lecture 7 because we're giving Claude the ability to request function execution:

```
<span></span><span># Ask Claude a question that requires our function</span>
<span>message</span> <span>=</span> <span>client</span><span>.</span><span>messages</span><span>.</span><span>create</span><span>(</span>
    <span>model</span><span>=</span><span>"claude-sonnet-4-20250514"</span><span>,</span>
    <span>max_tokens</span><span>=</span><span>300</span><span>,</span>
    <span>tools</span><span>=</span><span>tools</span><span>,</span>  <span># NEW! This gives Claude access to our functions</span>
    <span>messages</span><span>=</span><span>[{</span>
        <span>"role"</span><span>:</span> <span>"user"</span><span>,</span> 
        <span>"content"</span><span>:</span> <span>"What is the distance to a star with a parallax of 0.05 arcseconds?"</span>
    <span>}]</span>
<span>)</span>

<span># The response type tells us what Claude wants to do</span>
<span>print</span><span>(</span><span>f</span><span>"Claude's response type: </span><span>{</span><span>message</span><span>.</span><span>stop_reason</span><span>}</span><span>"</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"Number of content blocks in response: </span><span>{</span><span>len</span><span>(</span><span>message</span><span>.</span><span>content</span><span>)</span><span>}</span><span>"</span><span>)</span>
```

```
Claude's response type: tool_use
Number of content blocks in response: 2
```

### Understanding the Tool Response Structure

When Claude wants to use a tool, it doesn't just return text like in Lecture 7. Instead, it returns a structured response with multiple "blocks." Some blocks contain text (Claude's thoughts), and some contain tool requests (functions Claude wants to run).

Let's examine this structure carefully:

```
<span></span><span># Let's examine what Claude sent back</span>
<span>if</span> <span>message</span><span>.</span><span>stop_reason</span> <span>==</span> <span>"tool_use"</span><span>:</span>
    <span>print</span><span>(</span><span>"Claude wants to use a function!</span><span>\n</span><span>"</span><span>)</span>
    
    <span># Look at each block in the response</span>
    <span>for</span> <span>i</span><span>,</span> <span>block</span> <span>in</span> <span>enumerate</span><span>(</span><span>message</span><span>.</span><span>content</span><span>):</span>
        <span>print</span><span>(</span><span>f</span><span>"Block </span><span>{</span><span>i</span><span>}</span><span>: Type = '</span><span>{</span><span>block</span><span>.</span><span>type</span><span>}</span><span>'"</span><span>)</span>
        
        <span># Text blocks contain Claude's reasoning</span>
        <span>if</span> <span>hasattr</span><span>(</span><span>block</span><span>,</span> <span>'text'</span><span>):</span>
            <span>print</span><span>(</span><span>f</span><span>"  Text content: </span><span>\"</span><span>{</span><span>block</span><span>.</span><span>text</span><span>}</span><span>\"</span><span>"</span><span>)</span>
        
        <span># Tool use blocks contain function requests</span>
        <span>if</span> <span>hasattr</span><span>(</span><span>block</span><span>,</span> <span>'name'</span><span>):</span>
            <span>print</span><span>(</span><span>f</span><span>"  Function to call: </span><span>{</span><span>block</span><span>.</span><span>name</span><span>}</span><span>"</span><span>)</span>
            <span>print</span><span>(</span><span>f</span><span>"  Arguments to pass: </span><span>{</span><span>block</span><span>.</span><span>input</span><span>}</span><span>"</span><span>)</span>
            <span>print</span><span>(</span><span>f</span><span>"  Unique ID for this call: </span><span>{</span><span>block</span><span>.</span><span>id</span><span>}</span><span>"</span><span>)</span>
<span>else</span><span>:</span>
    <span>print</span><span>(</span><span>"Claude responded with text only (no function needed)"</span><span>)</span>
```

```
Claude wants to use a function!

Block 0: Type = 'text'
  Text content: "I'll calculate the distance to the star using its parallax measurement."
Block 1: Type = 'tool_use'
  Function to call: parallax_to_distance
  Arguments to pass: {'parallax_arcsec': 0.05}
  Unique ID for this call: toolu_01Qeq9kDRMScNvCREttow4uc
```

Claude has told us it wants to use a function, but it hasn't actually run anything yet. We need to extract the tool request, execute our Python function, and send the result back. This gives us full control over what code actually runs:

```
<span></span><span># The tool use request is typically the last content block</span>
<span>tool_use</span> <span>=</span> <span>message</span><span>.</span><span>content</span><span>[</span><span>-</span><span>1</span><span>]</span>

<span>print</span><span>(</span><span>"Tool request details:"</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"  Function name: </span><span>{</span><span>tool_use</span><span>.</span><span>name</span><span>}</span><span>"</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"  Arguments: </span><span>{</span><span>tool_use</span><span>.</span><span>input</span><span>}</span><span>"</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"  Tool ID: </span><span>{</span><span>tool_use</span><span>.</span><span>id</span><span>}</span><span>"</span><span>)</span>
<span>print</span><span>(</span><span>"</span><span>\n</span><span>This ID is important - we need it to send results back to Claude!"</span><span>)</span>
```

```
Tool request details:
  Function name: parallax_to_distance
  Arguments: {'parallax_arcsec': 0.05}
  Tool ID: toolu_01Qeq9kDRMScNvCREttow4uc

This ID is important - we need it to send results back to Claude!
```

### Executing the Function

Now we need to execute our function with the arguments Claude provided. Claude sends arguments as a dictionary like `{'parallax_arcsec': 0.05}`. We can extract the value and call our function:

```
<span></span><span># Execute our function with Claude's arguments</span>
<span>print</span><span>(</span><span>f</span><span>"Claude wants to call: </span><span>{</span><span>tool_use</span><span>.</span><span>name</span><span>}</span><span> with </span><span>{</span><span>tool_use</span><span>.</span><span>input</span><span>}</span><span>"</span><span>)</span>

<span># Extract the parallax value from the dictionary</span>
<span>parallax_value</span> <span>=</span> <span>tool_use</span><span>.</span><span>input</span><span>[</span><span>'parallax_arcsec'</span><span>]</span>
<span>print</span><span>(</span><span>f</span><span>"Extracted parallax value: </span><span>{</span><span>parallax_value</span><span>}</span><span>"</span><span>)</span>

<span># Call our function</span>
<span>result</span> <span>=</span> <span>parallax_to_distance</span><span>(</span><span>parallax_value</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"Function result: </span><span>{</span><span>result</span><span>}</span><span>"</span><span>)</span>
```

```
Claude wants to call: parallax_to_distance with {'parallax_arcsec': 0.05}
Extracted parallax value: 0.05
Function result: {'distance_parsecs': 20.0}
```

### Completing the Conversation with Natural Language

This is a crucial step: we need to send the function result back to Claude so it can formulate a complete, natural language answer. Without this step, the user would just see raw function output instead of a helpful explanation. This is what transforms a simple calculation into a conversational response:

```
<span></span><span># Continue the conversation by sending the function result back to Claude</span>
<span>final_response</span> <span>=</span> <span>client</span><span>.</span><span>messages</span><span>.</span><span>create</span><span>(</span>
    <span>model</span><span>=</span><span>"claude-sonnet-4-20250514"</span><span>,</span>
    <span>max_tokens</span><span>=</span><span>200</span><span>,</span>
    <span>tools</span><span>=</span><span>tools</span><span>,</span>
    <span>messages</span><span>=</span><span>[</span>
        <span># The original user question</span>
        <span>{</span>
            <span>"role"</span><span>:</span> <span>"user"</span><span>,</span> 
            <span>"content"</span><span>:</span> <span>"What is the distance to a star with a parallax of 0.05 arcseconds?"</span>
        <span>},</span>
        <span># Claude's response requesting the function</span>
        <span>{</span>
            <span>"role"</span><span>:</span> <span>"assistant"</span><span>,</span> 
            <span>"content"</span><span>:</span> <span>message</span><span>.</span><span>content</span>
        <span>},</span>
        <span># Our function result sent back to Claude</span>
        <span>{</span>
            <span>"role"</span><span>:</span> <span>"user"</span><span>,</span> 
            <span>"content"</span><span>:</span> <span>[{</span>
                <span>"type"</span><span>:</span> <span>"tool_result"</span><span>,</span>
                <span>"tool_use_id"</span><span>:</span> <span>tool_use</span><span>.</span><span>id</span><span>,</span>  <span># Must match the original request ID</span>
                <span>"content"</span><span>:</span> <span>str</span><span>(</span><span>result</span><span>)</span>  <span># Convert result to string</span>
            <span>}]</span>
        <span>}</span>
    <span>]</span>
<span>)</span>

<span>print</span><span>(</span><span>"Claude's final natural language answer:"</span><span>)</span>
<span>print</span><span>(</span><span>"="</span> <span>*</span> <span>50</span><span>)</span>
<span>print</span><span>(</span><span>final_response</span><span>.</span><span>content</span><span>[</span><span>0</span><span>]</span><span>.</span><span>text</span><span>)</span>
<span>print</span><span>(</span><span>"="</span> <span>*</span> <span>50</span><span>)</span>
<span>print</span><span>(</span><span>"</span><span>\n</span><span>Notice how Claude converts the raw number into a complete explanation!"</span><span>)</span>
```

```
Claude's final natural language answer:
==================================================
The distance to a star with a parallax of 0.05 arcseconds is **20 parsecs**.

To put this in perspective:
- 20 parsecs = approximately 65.2 light-years
- This is a relatively nearby star in astronomical terms
- For comparison, the nearest star to our Sun (Proxima Centauri) is about 1.3 parsecs away

The relationship used here is the fundamental parallax-distance formula: distance (in parsecs) = 1 / parallax (in arcseconds).
==================================================

Notice how Claude converts the raw number into a complete explanation!
```

## Building Multiple Astronomical Functions

Now that you understand the complete workflow—from function definition to natural language response—let's expand your toolkit with more astronomical calculations. We'll see how Claude intelligently chooses between different functions based on the question.

### Adding a Stellar Luminosity Calculator

The Stefan-Boltzmann law tells us that a star's luminosity depends on its size and temperature. Specifically, L = 4πR²σT⁴, where σ is the Stefan-Boltzmann constant. This fundamental relationship lets us calculate how much energy a star emits:

```
<span></span><span>def</span><span> </span><span>stellar_luminosity</span><span>(</span><span>radius_solar</span><span>,</span> <span>temperature_k</span><span>):</span>
<span>    </span><span>"""</span>
<span>    Calculate stellar luminosity using the Stefan-Boltzmann law.</span>
<span>    </span>
<span>    The energy radiated by a star depends on its surface area (4πR²)</span>
<span>    and how much energy each square meter emits (σT⁴).</span>
<span>    """</span>
    <span># Physical constants</span>
    <span>stefan_boltzmann</span> <span>=</span> <span>5.67e-8</span>  <span># W m^-2 K^-4 (Stefan-Boltzmann constant)</span>
    <span>solar_radius</span> <span>=</span> <span>6.96e8</span>  <span># meters (Sun's radius)</span>
    <span>solar_luminosity</span> <span>=</span> <span>3.83e26</span>  <span># watts (Sun's total energy output)</span>
    
    <span># Always validate inputs</span>
    <span>if</span> <span>radius_solar</span> <span>&lt;=</span> <span>0</span> <span>or</span> <span>temperature_k</span> <span>&lt;=</span> <span>0</span><span>:</span>
        <span>return</span> <span>{</span><span>"error"</span><span>:</span> <span>"Radius and temperature must be positive"</span><span>}</span>
    
    <span># Convert stellar radius from solar units to meters</span>
    <span>radius_meters</span> <span>=</span> <span>radius_solar</span> <span>*</span> <span>solar_radius</span>
    
    <span># Apply Stefan-Boltzmann law: L = 4πR²σT⁴</span>
    <span>luminosity_watts</span> <span>=</span> <span>4</span> <span>*</span> <span>np</span><span>.</span><span>pi</span> <span>*</span> <span>radius_meters</span><span>**</span><span>2</span> <span>*</span> <span>stefan_boltzmann</span> <span>*</span> <span>temperature_k</span><span>**</span><span>4</span>
    
    <span># Convert to solar luminosities for easier interpretation</span>
    <span>luminosity_solar</span> <span>=</span> <span>luminosity_watts</span> <span>/</span> <span>solar_luminosity</span>
    
    <span>return</span> <span>{</span>
        <span>"luminosity_solar"</span><span>:</span> <span>round</span><span>(</span><span>luminosity_solar</span><span>,</span> <span>3</span><span>),</span>
        <span>"luminosity_watts"</span><span>:</span> <span>f</span><span>"</span><span>{</span><span>luminosity_watts</span><span>:</span><span>.2e</span><span>}</span><span>"</span>  <span># Scientific notation</span>
    <span>}</span>
```

Let's verify our function works correctly by testing it with the Sun's values:

```
<span></span><span># Test with the Sun (should give ~1.0 solar luminosity)</span>
<span>sun_test</span> <span>=</span> <span>stellar_luminosity</span><span>(</span><span>1.0</span><span>,</span> <span>5778</span><span>)</span>  <span># Sun: 1 solar radius, 5778 K</span>
<span>print</span><span>(</span><span>f</span><span>"Sun's calculated luminosity: </span><span>{</span><span>sun_test</span><span>[</span><span>'luminosity_solar'</span><span>]</span><span>}</span><span> L☉"</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"In watts: </span><span>{</span><span>sun_test</span><span>[</span><span>'luminosity_watts'</span><span>]</span><span>}</span><span> W"</span><span>)</span>
<span>print</span><span>(</span><span>"(Should be very close to 1.0 solar luminosity!)"</span><span>)</span>

<span># Test with a red giant</span>
<span>red_giant</span> <span>=</span> <span>stellar_luminosity</span><span>(</span><span>25</span><span>,</span> <span>3500</span><span>)</span>  <span># Typical red giant values</span>
<span>print</span><span>(</span><span>f</span><span>"</span><span>\n</span><span>Red giant luminosity: </span><span>{</span><span>red_giant</span><span>[</span><span>'luminosity_solar'</span><span>]</span><span>}</span><span> L☉"</span><span>)</span>
<span>print</span><span>(</span><span>"(Much brighter than the Sun despite being cooler, due to larger size)"</span><span>)</span>
```

```
Sun's calculated luminosity: 1.004 L☉
In watts: 3.85e+26 W
(Should be very close to 1.0 solar luminosity!)

Red giant luminosity: 84.521 L☉
(Much brighter than the Sun despite being cooler, due to larger size)
```

### Updating the Tools List

Now we need to tell Claude about both functions. Claude will automatically learn to choose the right function based on the question content—questions about distance will trigger the parallax function, while questions about brightness will trigger the luminosity function:

```
<span></span><span># Expanded tools list with both functions</span>
<span>tools</span> <span>=</span> <span>[</span>
    <span>{</span>
        <span>"name"</span><span>:</span> <span>"parallax_to_distance"</span><span>,</span>
        <span>"description"</span><span>:</span> <span>"Calculate stellar distance from parallax measurement"</span><span>,</span>
        <span>"input_schema"</span><span>:</span> <span>{</span>
            <span>"type"</span><span>:</span> <span>"object"</span><span>,</span>
            <span>"properties"</span><span>:</span> <span>{</span>
                <span>"parallax_arcsec"</span><span>:</span> <span>{</span>
                    <span>"type"</span><span>:</span> <span>"number"</span><span>,</span>
                    <span>"description"</span><span>:</span> <span>"Parallax in arcseconds (must be positive)"</span>
                <span>}</span>
            <span>},</span>
            <span>"required"</span><span>:</span> <span>[</span><span>"parallax_arcsec"</span><span>]</span>
        <span>}</span>
    <span>},</span>
    <span>{</span>
        <span>"name"</span><span>:</span> <span>"stellar_luminosity"</span><span>,</span> 
        <span>"description"</span><span>:</span> <span>"Calculate stellar luminosity from radius and temperature"</span><span>,</span>
        <span>"input_schema"</span><span>:</span> <span>{</span>
            <span>"type"</span><span>:</span> <span>"object"</span><span>,</span>
            <span>"properties"</span><span>:</span> <span>{</span>
                <span>"radius_solar"</span><span>:</span> <span>{</span>
                    <span>"type"</span><span>:</span> <span>"number"</span><span>,</span>
                    <span>"description"</span><span>:</span> <span>"Stellar radius in solar radii"</span>
                <span>},</span>
                <span>"temperature_k"</span><span>:</span> <span>{</span>
                    <span>"type"</span><span>:</span> <span>"number"</span><span>,</span> 
                    <span>"description"</span><span>:</span> <span>"Effective temperature in Kelvin"</span>
                <span>}</span>
            <span>},</span>
            <span>"required"</span><span>:</span> <span>[</span><span>"radius_solar"</span><span>,</span> <span>"temperature_k"</span><span>]</span>
        <span>}</span>
    <span>}</span>
<span>]</span>

<span>print</span><span>(</span><span>f</span><span>"Claude now has access to </span><span>{</span><span>len</span><span>(</span><span>tools</span><span>)</span><span>}</span><span> functions:"</span><span>)</span>
<span>for</span> <span>tool</span> <span>in</span> <span>tools</span><span>:</span>
    <span>print</span><span>(</span><span>f</span><span>"  • </span><span>{</span><span>tool</span><span>[</span><span>'name'</span><span>]</span><span>}</span><span>"</span><span>)</span>
```

```
Claude now has access to 2 functions:
  • parallax_to_distance
  • stellar_luminosity
```

### Creating a Complete Tool Execution Helper

Since we'll be executing tools frequently, let's create a helper function that handles the complete workflow from question to natural language answer. This will make our code cleaner, avoid repetition, and ensure we always get natural language responses:

```
<span></span><span>def</span><span> </span><span>execute_tool_and_respond</span><span>(</span><span>question</span><span>,</span> <span>tools</span><span>):</span>
<span>    </span><span>"""</span>
<span>    Complete workflow: question → tool execution → natural language answer.</span>
<span>    </span>
<span>    This function handles the entire process we've been doing manually:</span>
<span>    1. Send question to Claude</span>
<span>    2. Execute requested function if needed</span>
<span>    3. Get natural language response</span>
<span>    """</span>
    <span># Step 1: Ask Claude the question</span>
    <span>initial_response</span> <span>=</span> <span>client</span><span>.</span><span>messages</span><span>.</span><span>create</span><span>(</span>
        <span>model</span><span>=</span><span>"claude-sonnet-4-20250514"</span><span>,</span>
        <span>max_tokens</span><span>=</span><span>300</span><span>,</span>
        <span>tools</span><span>=</span><span>tools</span><span>,</span>
        <span>messages</span><span>=</span><span>[{</span><span>"role"</span><span>:</span> <span>"user"</span><span>,</span> <span>"content"</span><span>:</span> <span>question</span><span>}]</span>
    <span>)</span>
    
    <span># Check if Claude wants to use a tool</span>
    <span>if</span> <span>initial_response</span><span>.</span><span>stop_reason</span> <span>!=</span> <span>"tool_use"</span><span>:</span>
        <span># No tool needed, return direct response</span>
        <span>return</span> <span>initial_response</span><span>.</span><span>content</span><span>[</span><span>0</span><span>]</span><span>.</span><span>text</span>
    
    <span># Step 2: Execute the requested function</span>
    <span>tool_use</span> <span>=</span> <span>initial_response</span><span>.</span><span>content</span><span>[</span><span>-</span><span>1</span><span>]</span>
    
    <span># Execute the appropriate function based on name</span>
    <span>if</span> <span>tool_use</span><span>.</span><span>name</span> <span>==</span> <span>"parallax_to_distance"</span><span>:</span>
        <span># Extract the parallax value and call function</span>
        <span>parallax</span> <span>=</span> <span>tool_use</span><span>.</span><span>input</span><span>[</span><span>'parallax_arcsec'</span><span>]</span>
        <span>result</span> <span>=</span> <span>parallax_to_distance</span><span>(</span><span>parallax</span><span>)</span>
    <span>elif</span> <span>tool_use</span><span>.</span><span>name</span> <span>==</span> <span>"stellar_luminosity"</span><span>:</span>
        <span># Extract both parameters and call function</span>
        <span>radius</span> <span>=</span> <span>tool_use</span><span>.</span><span>input</span><span>[</span><span>'radius_solar'</span><span>]</span>
        <span>temp</span> <span>=</span> <span>tool_use</span><span>.</span><span>input</span><span>[</span><span>'temperature_k'</span><span>]</span>
        <span>result</span> <span>=</span> <span>stellar_luminosity</span><span>(</span><span>radius</span><span>,</span> <span>temp</span><span>)</span>
    <span>else</span><span>:</span>
        <span>result</span> <span>=</span> <span>{</span><span>"error"</span><span>:</span> <span>f</span><span>"Unknown function: </span><span>{</span><span>tool_use</span><span>.</span><span>name</span><span>}</span><span>"</span><span>}</span>
    
    <span># Step 3: Send result back for natural language response</span>
    <span>final_response</span> <span>=</span> <span>client</span><span>.</span><span>messages</span><span>.</span><span>create</span><span>(</span>
        <span>model</span><span>=</span><span>"claude-sonnet-4-20250514"</span><span>,</span>
        <span>max_tokens</span><span>=</span><span>300</span><span>,</span>
        <span>tools</span><span>=</span><span>tools</span><span>,</span>
        <span>messages</span><span>=</span><span>[</span>
            <span>{</span><span>"role"</span><span>:</span> <span>"user"</span><span>,</span> <span>"content"</span><span>:</span> <span>question</span><span>},</span>
            <span>{</span><span>"role"</span><span>:</span> <span>"assistant"</span><span>,</span> <span>"content"</span><span>:</span> <span>initial_response</span><span>.</span><span>content</span><span>},</span>
            <span>{</span>
                <span>"role"</span><span>:</span> <span>"user"</span><span>,</span>
                <span>"content"</span><span>:</span> <span>[{</span>
                    <span>"type"</span><span>:</span> <span>"tool_result"</span><span>,</span>
                    <span>"tool_use_id"</span><span>:</span> <span>tool_use</span><span>.</span><span>id</span><span>,</span>
                    <span>"content"</span><span>:</span> <span>str</span><span>(</span><span>result</span><span>)</span>
                <span>}]</span>
            <span>}</span>
        <span>]</span>
    <span>)</span>
    
    <span>return</span> <span>final_response</span><span>.</span><span>content</span><span>[</span><span>0</span><span>]</span><span>.</span><span>text</span>
```

Now let's test our complete workflow with different astronomical questions to see Claude choose the right tool and provide natural language answers:

```
<span></span><span># Test different types of questions</span>
<span>test_questions</span> <span>=</span> <span>[</span>
    <span>"What's the distance to Proxima Centauri if its parallax is 0.768 arcseconds?"</span><span>,</span>
    <span>"Calculate the luminosity of Betelgeuse with radius 700 solar radii and temperature 3500 K"</span>
<span>]</span>

<span>for</span> <span>question</span> <span>in</span> <span>test_questions</span><span>:</span>
    <span>print</span><span>(</span><span>f</span><span>"Question: </span><span>{</span><span>question</span><span>}</span><span>"</span><span>)</span>
    <span>print</span><span>(</span><span>"</span><span>\n</span><span>Answer:"</span><span>)</span>
    <span>answer</span> <span>=</span> <span>execute_tool_and_respond</span><span>(</span><span>question</span><span>,</span> <span>tools</span><span>)</span>
    <span>print</span><span>(</span><span>answer</span><span>)</span>
    <span>print</span><span>(</span><span>"</span><span>\n</span><span>"</span> <span>+</span> <span>"="</span><span>*</span><span>70</span> <span>+</span> <span>"</span><span>\n</span><span>"</span><span>)</span>
```

```
Question: What's the distance to Proxima Centauri if its parallax is 0.768 arcseconds?

Answer:
```

```
Based on a parallax of 0.768 arcseconds, Proxima Centauri is approximately **1.3 parsecs** away from Earth.

To put this in perspective:
- 1.3 parsecs = about 4.2 light-years
- This makes Proxima Centauri the closest known star to our Solar System (excluding the Sun)

The distance calculation uses the parallax formula: distance (in parsecs) = 1 / parallax (in arcseconds), which is why the larger parallax angle of 0.768" corresponds to this relatively close distance.

======================================================================

Question: Calculate the luminosity of Betelgeuse with radius 700 solar radii and temperature 3500 K

Answer:
```

```
Based on the calculations, Betelgeuse has a luminosity of approximately **66,264 solar luminosities** (L☉), which equals about **2.54 × 10³¹ watts**.

This extremely high luminosity is due to Betelgeuse's enormous size - despite having a relatively cool surface temperature of 3,500 K (compared to the Sun's 5,778 K), its massive radius of 700 solar radii gives it a total surface area that is 490,000 times larger than the Sun's. This enormous surface area more than compensates for the lower temperature, making Betelgeuse one of the most luminous stars known.

======================================================================

```

## Introduction to RAG (Retrieval Augmented Generation)

After seven weeks of lectures, you've accumulated a wealth of knowledge: Python fundamentals, NumPy operations, visualization techniques, and API usage. But here's a familiar problem: when working on your research projects and you need to remember "How did we handle errors in Lecture 3?" or "What was that matplotlib syntax from Lecture 6?", you end up with twenty browser tabs open, scrolling through notebooks trying to find that one code example.

This is exactly the problem that RAG (Retrieval Augmented Generation) solves. RAG combines document search with LLM reasoning, allowing you to ask questions like "Find all the error handling techniques we learned" and get comprehensive answers drawn directly from your course materials.

### What is RAG?

RAG stands for Retrieval Augmented Generation. Think of it as giving Claude access to your personal textbook—not just its general knowledge, but your specific lecture notes and examples.

The process has three steps:

1.  **Retrieval**: Search through your documents to find relevant sections
2.  **Augmentation**: Add those relevant sections to your question as context
3.  **Generation**: Have Claude answer using both its knowledge and your specific materials

Without RAG, if you ask Claude "What did we learn about the temperature parameter?", it can only give general information about temperature parameters in LLMs. With RAG, it can tell you exactly what YOUR lecture notes say, with the specific examples and explanations from class.

### Understanding Markdown Files (.md)

Before we work with our lecture materials, let's understand what a markdown file is. You've actually been using markdown all semester—every text cell in your Jupyter notebooks uses markdown formatting!

**What is a .md file?** A markdown file (with the extension .md) is a plain text file that uses simple symbols for formatting:

-   `#` for headers (like `# Title` or `## Section`)
-   `*` for italics and `**` for bold
-   Three backticks (\`\`\`) for code blocks
-   `-` for bullet points

The beauty of markdown is that it's human-readable even without rendering. You can open a .md file in any text editor (like Cursor, Notepad, or TextEdit) and read it easily.

### Converting Jupyter Notebooks to Markdown with Jupytext

Your lecture materials are currently in Jupyter notebook format (.ipynb files), which contain both code and text mixed with metadata and output. To make them searchable for RAG, we need to convert them to plain markdown.

**Jupytext** is a tool that converts between different notebook formats. Think of it as a translator that can turn your .ipynb files into clean .md files. Here's how to use it:

First, install Jupytext:

To convert your notebook files to markdown, you would use Jupytext from the terminal:

```
<span></span>jupytext<span> </span>--to<span> </span>md<span> </span>Lecture7_LLM_API_Basics_20250924.ipynb
```

This creates a file called `Lecture7_LLM_API_Basics_20250924.md` in the same folder. The markdown file contains all your text cells and code cells from the notebook, but in a clean text format perfect for searching.

For this lecture, we've already converted Lecture 7 to markdown format, so we can work with it directly. Let's read this file:

```
<span></span><span># Read the pre-converted lecture file</span>
<span>with</span> <span>open</span><span>(</span><span>'Lecture7_LLM_API_Basics_20250924.md'</span><span>,</span> <span>'r'</span><span>)</span> <span>as</span> <span>f</span><span>:</span>
    <span>lecture7_content</span> <span>=</span> <span>f</span><span>.</span><span>read</span><span>()</span>
```

Markdown uses `#` symbols for headers. In our lecture file:

-   `#` marks the main title
-   `##` marks major sections
-   `###` marks subsections

Let's find all the main topics covered in Lecture 7 using simple string methods you learned in Lecture 2:

```
<span></span><span># Find all main sections using string methods</span>
<span>sections</span> <span>=</span> <span>[]</span>
<span>lines</span> <span>=</span> <span>lecture7_content</span><span>.</span><span>split</span><span>(</span><span>'</span><span>\n</span><span>'</span><span>)</span>  <span># Split into individual lines</span>

<span>for</span> <span>line</span> <span>in</span> <span>lines</span><span>:</span>
    <span># Check if line starts with '## ' (main section header)</span>
    <span>if</span> <span>line</span><span>.</span><span>startswith</span><span>(</span><span>'## '</span><span>):</span>
        <span># Remove the '## ' to get just the title</span>
        <span>section_title</span> <span>=</span> <span>line</span><span>[</span><span>3</span><span>:]</span>  <span># Everything after '## '</span>
        <span>sections</span><span>.</span><span>append</span><span>(</span><span>section_title</span><span>)</span>

<span>print</span><span>(</span><span>f</span><span>"Found </span><span>{</span><span>len</span><span>(</span><span>sections</span><span>)</span><span>}</span><span> main sections in Lecture 7:"</span><span>)</span>
<span>print</span><span>()</span>
<span>for</span> <span>i</span><span>,</span> <span>section</span> <span>in</span> <span>enumerate</span><span>(</span><span>sections</span><span>[:</span><span>8</span><span>],</span> <span>1</span><span>):</span>  <span># Show first 8</span>
    <span>print</span><span>(</span><span>f</span><span>"  </span><span>{</span><span>i</span><span>}</span><span>. </span><span>{</span><span>section</span><span>}</span><span>"</span><span>)</span>
<span>if</span> <span>len</span><span>(</span><span>sections</span><span>)</span> <span>&gt;</span> <span>8</span><span>:</span>
    <span>print</span><span>(</span><span>f</span><span>"  ... and </span><span>{</span><span>len</span><span>(</span><span>sections</span><span>)</span><span> </span><span>-</span><span> </span><span>8</span><span>}</span><span> more sections"</span><span>)</span>
```

```
Found 11 main sections in Lecture 7:

  1. Introduction
  2. Understanding APIs
  3. Setting Up Your Connection
  4. Your First API Call
  5. Understanding the Parameters
  6. Building Conversations
  7. Prompting Strategies
  8. Making It Practical
  ... and 3 more sections
```

## Document Chunking

### Why We Need to Chunk Documents

Our Lecture 7 file contains tens of thousands of characters—that's enormous! Sending the entire document to Claude every time we ask a question would create three major problems:

1.  **Cost**: We'd be paying for all those characters as input tokens for every single question, even if we're only asking about one small topic
2.  **Relevance**: If you ask about "API errors", 95% of the document isn't relevant—it's about other topics like image processing or conversation management
3.  **Focus**: Claude performs better with focused, relevant context rather than being overwhelmed with unrelated information

The solution is **document chunking**—breaking the large document into smaller, manageable pieces. Think of it like organizing a library: instead of reading every page of every book to answer a question, you first identify which chapter or section is most relevant.

### Simple Section-Based Chunking

The simplest chunking strategy is to split by section headers. Each section of the lecture becomes its own searchable chunk. This works well for structured documents like lecture notes where each section covers a specific topic.

Let's implement this approach:

```
<span></span><span>def</span><span> </span><span>chunk_by_sections</span><span>(</span><span>text</span><span>):</span>
<span>    </span><span>"""</span>
<span>    Split a document into chunks based on ## section headers.</span>
<span>    </span>
<span>    This function:</span>
<span>    1. Finds all the ## headers in the text</span>
<span>    2. Splits the document at these headers</span>
<span>    3. Keeps each section as a separate chunk</span>
<span>    4. Preserves the section header with its content</span>
<span>    """</span>
    <span># Split on section headers</span>
    <span># We use '\n## ' to ensure we're splitting on headers at line starts</span>
    <span>sections</span> <span>=</span> <span>text</span><span>.</span><span>split</span><span>(</span><span>'</span><span>\n</span><span>## '</span><span>)</span>
    
    <span>chunks</span> <span>=</span> <span>[]</span>
    <span>for</span> <span>i</span><span>,</span> <span>section</span> <span>in</span> <span>enumerate</span><span>(</span><span>sections</span><span>):</span>
        <span># The first section doesn't have '## ' removed (it wasn't split)</span>
        <span>if</span> <span>i</span> <span>==</span> <span>0</span><span>:</span>
            <span>chunk_text</span> <span>=</span> <span>section</span>
        <span>else</span><span>:</span>
            <span># Add back the '## ' that was removed during split</span>
            <span>chunk_text</span> <span>=</span> <span>'## '</span> <span>+</span> <span>section</span>
        
        <span># Only keep chunks with substantial content (at least 100 characters)</span>
        <span>if</span> <span>len</span><span>(</span><span>chunk_text</span><span>.</span><span>strip</span><span>())</span> <span>&gt;</span> <span>100</span><span>:</span>
            <span>chunks</span><span>.</span><span>append</span><span>({</span>
                <span>'text'</span><span>:</span> <span>chunk_text</span><span>.</span><span>strip</span><span>(),</span>
                <span>'length'</span><span>:</span> <span>len</span><span>(</span><span>chunk_text</span><span>),</span>
                <span>'chunk_id'</span><span>:</span> <span>i</span>
            <span>})</span>
    
    <span>return</span> <span>chunks</span>
```

```
<span></span><span># Create chunks from our lecture</span>
<span>lecture_chunks</span> <span>=</span> <span>chunk_by_sections</span><span>(</span><span>lecture7_content</span><span>)</span>

<span>print</span><span>(</span><span>f</span><span>"Created </span><span>{</span><span>len</span><span>(</span><span>lecture_chunks</span><span>)</span><span>}</span><span> chunks from Lecture 7"</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"</span><span>\n</span><span>Chunk statistics:"</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"  Average size: </span><span>{</span><span>sum</span><span>(</span><span>c</span><span>[</span><span>'length'</span><span>]</span><span> </span><span>for</span><span> </span><span>c</span><span> </span><span>in</span><span> </span><span>lecture_chunks</span><span>)</span><span> </span><span>//</span><span> </span><span>len</span><span>(</span><span>lecture_chunks</span><span>)</span><span>:</span><span>,</span><span>}</span><span> characters"</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"  Smallest: </span><span>{</span><span>min</span><span>(</span><span>c</span><span>[</span><span>'length'</span><span>]</span><span> </span><span>for</span><span> </span><span>c</span><span> </span><span>in</span><span> </span><span>lecture_chunks</span><span>)</span><span>:</span><span>,</span><span>}</span><span> characters"</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"  Largest: </span><span>{</span><span>max</span><span>(</span><span>c</span><span>[</span><span>'length'</span><span>]</span><span> </span><span>for</span><span> </span><span>c</span><span> </span><span>in</span><span> </span><span>lecture_chunks</span><span>)</span><span>:</span><span>,</span><span>}</span><span> characters"</span><span>)</span>
```

```
Created 12 chunks from Lecture 7

Chunk statistics:
  Average size: 5,275 characters
  Smallest: 323 characters
  Largest: 9,570 characters
```

Let's examine what our chunks look like to understand what we've created:

```
<span></span><span># Examine the first few chunks</span>
<span>print</span><span>(</span><span>"First 3 chunks from Lecture 7:"</span><span>)</span>
<span>print</span><span>(</span><span>"="</span> <span>*</span> <span>50</span><span>)</span>

<span>for</span> <span>i</span> <span>in</span> <span>range</span><span>(</span><span>min</span><span>(</span><span>3</span><span>,</span> <span>len</span><span>(</span><span>lecture_chunks</span><span>))):</span>
    <span>chunk</span> <span>=</span> <span>lecture_chunks</span><span>[</span><span>i</span><span>]</span>
    <span># Get the first line (usually the section title)</span>
    <span>first_line</span> <span>=</span> <span>chunk</span><span>[</span><span>'text'</span><span>]</span><span>.</span><span>split</span><span>(</span><span>'</span><span>\n</span><span>'</span><span>)[</span><span>0</span><span>]</span>
    
    <span>print</span><span>(</span><span>f</span><span>"</span><span>\n</span><span>Chunk </span><span>{</span><span>i</span><span>}</span><span>:"</span><span>)</span>
    <span>print</span><span>(</span><span>f</span><span>"  Title: </span><span>{</span><span>first_line</span><span>}</span><span>"</span><span>)</span>
    <span>print</span><span>(</span><span>f</span><span>"  Size: </span><span>{</span><span>chunk</span><span>[</span><span>'length'</span><span>]</span><span>:</span><span>,</span><span>}</span><span> characters"</span><span>)</span>
    <span>print</span><span>(</span><span>f</span><span>"  Preview: </span><span>{</span><span>chunk</span><span>[</span><span>'text'</span><span>][:</span><span>150</span><span>]</span><span>}</span><span>..."</span><span>)</span>
```

```
First 3 chunks from Lecture 7:
==================================================

Chunk 0:
  Title: ---
  Size: 323 characters
  Preview: ---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version:...

Chunk 1:
  Title: ## Introduction
  Size: 5,969 characters
  Preview: ## Introduction

For the past six weeks, you've been building a programming foundation. Variables, lists, loops, functions, classes—perhaps they felt ...

Chunk 2:
  Title: ## Understanding APIs
  Size: 3,336 characters
  Preview: ## Understanding APIs

Let's demystify this term that gets thrown around constantly in programming. API stands for Application Programming Interface, ...
```

### Understanding Overlapping Chunks

A potential problem with simple splitting: what if important information spans across chunk boundaries? Imagine reading a textbook where each chapter ends mid-sentence—you'd lose crucial context!

**Overlapping chunks** solve this by having each chunk include some content from its neighbors. It's like having each chapter of a book reprint the last paragraph of the previous chapter and the first paragraph of the next chapter. This ensures nothing important gets lost in the gaps between chunks.

Here's a visual example:

```sql
Original text: "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
Non-overlapping chunks of size 10:
  Chunk 1: "ABCDEFGHIJ"
  Chunk 2: "KLMNOPQRST"
  Chunk 3: "UVWXYZ"
  
Overlapping chunks (size 10, overlap 3):
  Chunk 1: "ABCDEFGHIJ"
  Chunk 2: "HIJKLMNOPQ"  (starts at H, overlaps HIJ)
  Chunk 3: "OPQRSTUVWX"  (starts at O, overlaps OPQ)
```

While overlapping chunks are more sophisticated and useful for many applications, for our lecture materials that are already well-structured with clear section boundaries, simple section-based chunking works well.

## Understanding Embeddings

Now we have chunks of text, but how do we find which chunks are relevant to a user's question? We can't just search for exact word matches—what if someone asks about "error handling" but the text says "exception management"? These mean the same thing but use different words.

This is where **embeddings** come in. An embedding is a way to convert text into a list of numbers (called a vector) that captures the semantic meaning of that text. The key insight: texts with similar meanings will have similar number patterns, even if they use different words.

Think of it like this:

-   "stellar parallax" might become \[0.2, -0.1, 0.8, 0.3, ..., 0.5\] (384 numbers)
-   "star distance measurement" might become \[0.3, -0.2, 0.7, 0.4, ..., 0.4\] (384 numbers)
-   "cooking recipes" might become \[0.9, 0.5, -0.3, 0.1, ..., -0.2\] (384 numbers)

Notice how the first two (both about measuring star distances) have similar number patterns, while the third (about cooking) is completely different. The embedding model has learned that "parallax" and "distance measurement" are related concepts in astronomy.

### How Embeddings Capture Meaning

Embedding models are neural networks trained on millions of documents. Through this training, they learn:

-   "API" and "programming interface" are related concepts
-   "error" and "exception" often mean similar things in programming
-   "temperature" in the context of LLMs is different from "temperature" in physics

Each dimension in the embedding vector captures some aspect of meaning. While we can't interpret what each individual number means (they're learned by the neural network), we can measure how similar two embeddings are to find related texts.

### Important Note: Normalized Embeddings

Most modern embedding models, including the one we'll use, output **normalized vectors**. This means all embedding vectors have a magnitude (length) of 1.0. This is a crucial property that simplifies our calculations significantly!

### Important Tip: Complete Sentences Give Better Embeddings

When creating embeddings, **complete sentences often work better than keywords!** The embedding model can better understand context and meaning from full sentences. For example:

-   "How to measure stellar parallax?" gives richer embeddings than just "parallax"
-   "What are the error handling techniques in Python?" is better than "error handling"

This is because the model was trained on natural language text, so it better understands the relationships between words when they appear in complete thoughts.

### Measuring Similarity with Cosine Similarity

Once we have embeddings (vectors of numbers), we need to measure how similar they are. We use **cosine similarity**, which measures the angle between two vectors.

The intuition is simple:

-   Vectors pointing in the same direction = similar meaning (cosine similarity ≈ 1)
-   Vectors at right angles = unrelated (cosine similarity ≈ 0)
-   Vectors pointing opposite ways = opposite meanings (cosine similarity ≈ -1)

The mathematical formula is: cosine(θ) = (A·B) / (||A|| × ||B||)

Where:

-   A·B is the dot product (measures alignment)
-   ||A|| and ||B|| are the vector magnitudes (lengths)

**However, since embedding models output normalized vectors (||A|| = ||B|| = 1), the formula simplifies to just the dot product: cosine(θ) = A·B**

Let's implement the simplified version:

```
<span></span><span>def</span><span> </span><span>cosine_similarity</span><span>(</span><span>vec1</span><span>,</span> <span>vec2</span><span>):</span>
<span>    </span><span>"""</span>
<span>    Calculate cosine similarity for normalized vectors.</span>
<span>    Since ||vec1|| = ||vec2|| = 1, cosine similarity = dot product.</span>
<span>    Much faster and simpler!</span>
<span>    """</span>
    <span>return</span> <span>np</span><span>.</span><span>dot</span><span>(</span><span>vec1</span><span>,</span> <span>vec2</span><span>)</span>
```

### Using the Sentence-Transformers Library

To create actual embeddings that capture semantic meaning, we'll use a library called **sentence-transformers**. This library provides pre-trained neural network models that can convert any text into meaningful embedding vectors.

**What does sentence-transformers do?**

-   Provides ready-to-use embedding models trained on millions of documents
-   Handles all the complex neural network operations behind the scenes
-   Converts text to vectors that actually capture semantic meaning
-   Works with sentences, paragraphs, or entire documents

We'll use a model called **'all-MiniLM-L6-v2'** for this tutorial. Breaking down this name helps understand what we're working with: "all" means it works for all types of English text, "MiniLM" indicates it's a smaller, faster version of a language model, "L6" tells us it has 6 layers (the depth of the neural network), and "v2" simply means it's version 2, improved from the original.

**Importantly, this model outputs normalized vectors**, so we can use the simplified cosine similarity calculation.

This model converts any text into 384 numbers that capture its meaning. Through its training, it has learned that phrases like "stellar distance" and "how far away is the star" mean similar things, even though they use different words. We're using this particular model because it strikes the perfect balance for learning—it's small enough to run quickly on any computer (only 80MB download), fast enough for interactive experimentation, and powerful enough to demonstrate all RAG concepts effectively.

**More Powerful Models in Production**

In professional research and production systems, you'll often encounter more sophisticated embedding models. For example, OpenAI's text-embedding-3-large creates 3,072-dimensional embeddings compared to our 384, providing much richer semantic understanding. Google's text-embedding-004 produces 768-dimensional embeddings with excellent multilingual support. Specialized models like Voyage AI's voyage-3 or Cohere's embed-v3 offer 1,024 dimensions optimized for domain-specific or technical texts.

These larger models can capture more subtle semantic relationships and often perform better with specialized scientific literature. However, they come with trade-offs: they're more expensive (often requiring API payments), slower to run, require significantly more memory and storage, and are honestly overkill for learning the fundamental concepts.

Think of it like choosing a telescope: our all-MiniLM-L6-v2 is like a reliable 8-inch telescope that's perfect for learning astronomy. The production models are like research-grade observatories—more powerful, but you don't need them to understand how telescopes work! For your course projects and learning RAG concepts, our smaller model is perfectly adequate. When you eventually move to research-scale projects with thousands of papers, you can upgrade to these more powerful models using the exact same techniques you're learning today.

You can install the sentence-transformers library with the following command:

```
<span></span>pip<span> </span>install<span> </span>-q<span> </span>sentence-transformers
```

```
<span></span><span>from</span><span> </span><span>sentence_transformers</span><span> </span><span>import</span> <span>SentenceTransformer</span>

<span># Load a pre-trained embedding model</span>
<span>print</span><span>(</span><span>"Loading embedding model..."</span><span>)</span>
<span>print</span><span>(</span><span>"(First time will download ~80MB model file)"</span><span>)</span>
<span>embedding_model</span> <span>=</span> <span>SentenceTransformer</span><span>(</span><span>'all-MiniLM-L6-v2'</span><span>)</span>
<span>print</span><span>(</span><span>"✓ Model loaded successfully!"</span><span>)</span>

<span># Explore model properties</span>
<span>print</span><span>(</span><span>f</span><span>"</span><span>\n</span><span>Model information:"</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"  Output dimensions: </span><span>{</span><span>embedding_model</span><span>.</span><span>get_sentence_embedding_dimension</span><span>()</span><span>}</span><span>"</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"  Max input length: </span><span>{</span><span>embedding_model</span><span>.</span><span>max_seq_length</span><span>}</span><span> tokens"</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"  (A token is roughly a word or word piece)"</span><span>)</span>
```

```
Loading embedding model...
(First time will download ~80MB model file)
```

```
✓ Model loaded successfully!

Model information:
  Output dimensions: 384
  Max input length: 256 tokens
  (A token is roughly a word or word piece)
```

Let's test the embedding model to see how it captures semantic meaning:

```
<span></span><span># Test with astronomy concepts</span>
<span>test_texts</span> <span>=</span> <span>[</span>
    <span>"stellar parallax measurement"</span><span>,</span>
    <span>"measuring star distances"</span><span>,</span>  <span># Similar meaning, different words</span>
    <span>"galaxy classification"</span><span>,</span>      <span># Different astronomy topic</span>
    <span>"cooking recipes"</span>             <span># Completely unrelated</span>
<span>]</span>

<span># Generate embeddings</span>
<span>print</span><span>(</span><span>"Creating embeddings for test phrases..."</span><span>)</span>
<span>test_embeddings</span> <span>=</span> <span>[]</span>
<span>for</span> <span>text</span> <span>in</span> <span>test_texts</span><span>:</span>
    <span>embedding</span> <span>=</span> <span>embedding_model</span><span>.</span><span>encode</span><span>(</span><span>text</span><span>)</span>
    <span>test_embeddings</span><span>.</span><span>append</span><span>(</span><span>embedding</span><span>)</span>
    <span>print</span><span>(</span><span>f</span><span>"  '</span><span>{</span><span>text</span><span>}</span><span>': vector with </span><span>{</span><span>len</span><span>(</span><span>embedding</span><span>)</span><span>}</span><span> dimensions"</span><span>)</span>

<span># Verify that embeddings are normalized</span>
<span>print</span><span>(</span><span>"</span><span>\n</span><span>Checking if embeddings are normalized:"</span><span>)</span>
<span>for</span> <span>text</span><span>,</span> <span>embedding</span> <span>in</span> <span>zip</span><span>(</span><span>test_texts</span><span>,</span> <span>test_embeddings</span><span>):</span>
    <span>norm</span> <span>=</span> <span>np</span><span>.</span><span>linalg</span><span>.</span><span>norm</span><span>(</span><span>embedding</span><span>)</span>
    <span>print</span><span>(</span><span>f</span><span>"  '</span><span>{</span><span>text</span><span>}</span><span>': norm = </span><span>{</span><span>norm</span><span>:</span><span>.4f</span><span>}</span><span>"</span><span>)</span>

<span>print</span><span>(</span><span>"</span><span>\n</span><span>✓ All embeddings are normalized! We can use the simplified dot product for similarity."</span><span>)</span>
```

```
Creating embeddings for test phrases...
  'stellar parallax measurement': vector with 384 dimensions
  'measuring star distances': vector with 384 dimensions
```

```
  'galaxy classification': vector with 384 dimensions
  'cooking recipes': vector with 384 dimensions

Checking if embeddings are normalized:
  'stellar parallax measurement': norm = 1.0000
  'measuring star distances': norm = 1.0000
  'galaxy classification': norm = 1.0000
  'cooking recipes': norm = 1.0000

✓ All embeddings are normalized! We can use the simplified dot product for similarity.
```

```
<span></span><span># Calculate similarities between all pairs</span>
<span>print</span><span>(</span><span>"</span><span>\n</span><span>Semantic similarities between phrases:"</span><span>)</span>
<span>print</span><span>(</span><span>"="</span> <span>*</span> <span>50</span><span>)</span>

<span>for</span> <span>i</span> <span>in</span> <span>range</span><span>(</span><span>len</span><span>(</span><span>test_texts</span><span>)):</span>
    <span>for</span> <span>j</span> <span>in</span> <span>range</span><span>(</span><span>i</span><span>+</span><span>1</span><span>,</span> <span>len</span><span>(</span><span>test_texts</span><span>)):</span>
        <span>sim</span> <span>=</span> <span>cosine_similarity</span><span>(</span><span>test_embeddings</span><span>[</span><span>i</span><span>],</span> <span>test_embeddings</span><span>[</span><span>j</span><span>])</span>
        <span>print</span><span>(</span><span>f</span><span>"'</span><span>{</span><span>test_texts</span><span>[</span><span>i</span><span>]</span><span>}</span><span>' vs '</span><span>{</span><span>test_texts</span><span>[</span><span>j</span><span>]</span><span>}</span><span>'"</span><span>)</span>
        <span>print</span><span>(</span><span>f</span><span>"  Similarity: </span><span>{</span><span>sim</span><span>:</span><span>.3f</span><span>}</span><span>"</span><span>)</span>

<span>print</span><span>(</span><span>"</span><span>\n</span><span>Notice: 'stellar parallax' and 'star distances' have HIGH similarity!"</span><span>)</span>
<span>print</span><span>(</span><span>"The model understands they're about the same concept."</span><span>)</span>
```

```
Semantic similarities between phrases:
==================================================
'stellar parallax measurement' vs 'measuring star distances'
  Similarity: 0.622
'stellar parallax measurement' vs 'galaxy classification'
  Similarity: 0.333
'stellar parallax measurement' vs 'cooking recipes'
  Similarity: 0.020
'measuring star distances' vs 'galaxy classification'
  Similarity: 0.310
'measuring star distances' vs 'cooking recipes'
  Similarity: 0.048
'galaxy classification' vs 'cooking recipes'
  Similarity: 0.107

Notice: 'stellar parallax' and 'star distances' have HIGH similarity!
The model understands they're about the same concept.
```

## Building the Complete RAG System

Now let's combine everything we've learned to build a complete RAG system. We'll create embeddings for all our lecture chunks, build a search function that finds relevant content, and use that content to answer questions.

### Step 1: Create Embeddings for All Chunks

First, we need to convert every chunk of our lecture into an embedding vector. This is like creating an index for a book—we're preparing the content to be efficiently searchable. Each chunk gets converted to 384 numbers that capture its meaning:

```
<span></span><span># Generate embeddings for all lecture chunks</span>
<span>print</span><span>(</span><span>f</span><span>"Creating embeddings for </span><span>{</span><span>len</span><span>(</span><span>lecture_chunks</span><span>)</span><span>}</span><span> chunks..."</span><span>)</span>
<span>print</span><span>(</span><span>"This may take a minute...</span><span>\n</span><span>"</span><span>)</span>

<span>chunk_embeddings</span> <span>=</span> <span>[]</span>

<span>for</span> <span>i</span><span>,</span> <span>chunk</span> <span>in</span> <span>enumerate</span><span>(</span><span>lecture_chunks</span><span>):</span>
    <span># Create embedding for this chunk's text</span>
    <span># The encode() method converts text to a vector</span>
    <span>embedding</span> <span>=</span> <span>embedding_model</span><span>.</span><span>encode</span><span>(</span><span>chunk</span><span>[</span><span>'text'</span><span>])</span>
    <span>chunk_embeddings</span><span>.</span><span>append</span><span>(</span><span>embedding</span><span>)</span>
    
    <span># Show progress every 5 chunks</span>
    <span>if</span> <span>(</span><span>i</span> <span>+</span> <span>1</span><span>)</span> <span>%</span> <span>5</span> <span>==</span> <span>0</span><span>:</span>
        <span>print</span><span>(</span><span>f</span><span>"  Processed </span><span>{</span><span>i</span><span> </span><span>+</span><span> </span><span>1</span><span>}</span><span>/</span><span>{</span><span>len</span><span>(</span><span>lecture_chunks</span><span>)</span><span>}</span><span> chunks"</span><span>)</span>

<span>print</span><span>(</span><span>f</span><span>"</span><span>\n</span><span>✓ Created </span><span>{</span><span>len</span><span>(</span><span>chunk_embeddings</span><span>)</span><span>}</span><span> embeddings"</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"Each embedding has </span><span>{</span><span>len</span><span>(</span><span>chunk_embeddings</span><span>[</span><span>0</span><span>])</span><span>}</span><span> dimensions"</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"Total data: </span><span>{</span><span>len</span><span>(</span><span>chunk_embeddings</span><span>)</span><span>}</span><span> chunks × </span><span>{</span><span>len</span><span>(</span><span>chunk_embeddings</span><span>[</span><span>0</span><span>])</span><span>}</span><span> dimensions = </span><span>{</span><span>len</span><span>(</span><span>chunk_embeddings</span><span>)</span><span> </span><span>*</span><span> </span><span>len</span><span>(</span><span>chunk_embeddings</span><span>[</span><span>0</span><span>])</span><span>:</span><span>,</span><span>}</span><span> numbers"</span><span>)</span>
```

```
Creating embeddings for 12 chunks...
This may take a minute...

  Processed 5/12 chunks
```

```
  Processed 10/12 chunks

✓ Created 12 embeddings
Each embedding has 384 dimensions
Total data: 12 chunks × 384 dimensions = 4,608 numbers
```

### Step 2: Building the Search Function

Now we can build a search function that finds the most relevant chunks for any question. This is the "Retrieval" part of RAG. The process is:

1.  Convert the user's question to an embedding
2.  Compare it with all chunk embeddings using cosine similarity
3.  Return the chunks with the highest similarity scores

This is like having a librarian who understands meaning, not just keywords. If you ask about "error handling", it will find sections about "exceptions" and "try-except blocks" even if they don't use the exact phrase "error handling".

We'll use a vectorized approach for efficiency:

```
<span></span><span>def</span><span> </span><span>search_chunks</span><span>(</span><span>query</span><span>,</span> <span>top_k</span><span>=</span><span>3</span><span>):</span>
<span>    </span><span>"""</span>
<span>    Find the most relevant chunks for a query using vectorized operations.</span>
<span>    </span>
<span>    This function:</span>
<span>    1. Converts the query to an embedding (384 numbers)</span>
<span>    2. Calculates similarity with all chunk embeddings using vectorized NumPy</span>
<span>    3. Returns the top-k most similar chunks</span>
<span>    </span>
<span>    Parameters:</span>
<span>    - query: The search question</span>
<span>    - top_k: How many results to return</span>
<span>    """</span>
    <span># Convert query to embedding (same 384-dimensional space as chunks)</span>
    <span>query_embedding</span> <span>=</span> <span>embedding_model</span><span>.</span><span>encode</span><span>(</span><span>query</span><span>)</span>
    
    <span># Vectorized similarity calculation - much faster than a loop!</span>
    <span># Convert list of embeddings to NumPy array for vectorized operations</span>
    <span>chunk_matrix</span> <span>=</span> <span>np</span><span>.</span><span>array</span><span>(</span><span>chunk_embeddings</span><span>)</span>
    
    <span># Calculate dot products with all chunks at once</span>
    <span>similarities</span> <span>=</span> <span>np</span><span>.</span><span>dot</span><span>(</span><span>chunk_matrix</span><span>,</span> <span>query_embedding</span><span>)</span>
    
    <span># Find the indices of top-k highest similarities</span>
    <span># argsort() returns indices that would sort the array</span>
    <span># [-top_k:] takes the last k elements (highest values)</span>
    <span># [::-1] reverses to get descending order</span>
    <span>top_indices</span> <span>=</span> <span>np</span><span>.</span><span>argsort</span><span>(</span><span>similarities</span><span>)[</span><span>-</span><span>top_k</span><span>:][::</span><span>-</span><span>1</span><span>]</span>
    
    <span># Return the top chunks with their similarities</span>
    <span>results</span> <span>=</span> <span>[]</span>
    <span>for</span> <span>idx</span> <span>in</span> <span>top_indices</span><span>:</span>
        <span>results</span><span>.</span><span>append</span><span>({</span>
            <span>'chunk'</span><span>:</span> <span>lecture_chunks</span><span>[</span><span>idx</span><span>],</span>
            <span>'similarity'</span><span>:</span> <span>similarities</span><span>[</span><span>idx</span><span>]</span>
        <span>})</span>
    
    <span>return</span> <span>results</span>
```

### Step 3: Testing the Search

Let's test our search function with a specific question about API security from Lecture 7. This will show us which sections of the lecture are most relevant to our query:

```
<span></span><span># Test search with a specific question</span>
<span>query</span> <span>=</span> <span>"How do I keep API keys secure?"</span>
<span>results</span> <span>=</span> <span>search_chunks</span><span>(</span><span>query</span><span>,</span> <span>top_k</span><span>=</span><span>2</span><span>)</span>

<span>print</span><span>(</span><span>f</span><span>"Query: '</span><span>{</span><span>query</span><span>}</span><span>'"</span><span>)</span>
<span>print</span><span>(</span><span>"</span><span>\n</span><span>"</span> <span>+</span> <span>"="</span> <span>*</span> <span>50</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"Found </span><span>{</span><span>len</span><span>(</span><span>results</span><span>)</span><span>}</span><span> relevant sections:"</span><span>)</span>
<span>print</span><span>(</span><span>"="</span> <span>*</span> <span>50</span><span>)</span>

<span>for</span> <span>i</span><span>,</span> <span>result</span> <span>in</span> <span>enumerate</span><span>(</span><span>results</span><span>,</span> <span>1</span><span>):</span>
    <span># Extract section title (first line)</span>
    <span>lines</span> <span>=</span> <span>result</span><span>[</span><span>'chunk'</span><span>][</span><span>'text'</span><span>]</span><span>.</span><span>split</span><span>(</span><span>'</span><span>\n</span><span>'</span><span>)</span>
    <span>title</span> <span>=</span> <span>lines</span><span>[</span><span>0</span><span>]</span> <span>if</span> <span>lines</span> <span>else</span> <span>"No title"</span>
    
    <span>print</span><span>(</span><span>f</span><span>"</span><span>\n</span><span>Result </span><span>{</span><span>i</span><span>}</span><span>:"</span><span>)</span>
    <span>print</span><span>(</span><span>f</span><span>"  Similarity score: </span><span>{</span><span>result</span><span>[</span><span>'similarity'</span><span>]</span><span>:</span><span>.3f</span><span>}</span><span>"</span><span>)</span>
    <span>print</span><span>(</span><span>f</span><span>"  (1.0 = perfect match, 0.0 = unrelated)"</span><span>)</span>
    <span>print</span><span>(</span><span>f</span><span>"  Section: </span><span>{</span><span>title</span><span>}</span><span>"</span><span>)</span>
    <span>print</span><span>(</span><span>f</span><span>"  Preview: </span><span>{</span><span>result</span><span>[</span><span>'chunk'</span><span>][</span><span>'text'</span><span>][:</span><span>200</span><span>]</span><span>}</span><span>..."</span><span>)</span>
```

```
Query: 'How do I keep API keys secure?'

==================================================
Found 2 relevant sections:
==================================================

Result 1:
  Similarity score: 0.405
  (1.0 = perfect match, 0.0 = unrelated)
  Section: ## Summary
  Preview: ## Summary

### Key Concepts
In this lecture, you've learned:
- **API Fundamentals**: How to communicate with Large Language Models programmatically through structured requests and responses, transfor...

Result 2:
  Similarity score: 0.350
  (1.0 = perfect match, 0.0 = unrelated)
  Section: ## Understanding APIs
  Preview: ## Understanding APIs

Let's demystify this term that gets thrown around constantly in programming. API stands for Application Programming Interface, but that definition helps nobody. Here's a better ...
```

### Step 4: RAG-Powered Question Answering

Now for the complete RAG workflow. We'll create a function that combines everything:

1.  **Retrieval**: Search for relevant chunks from our lecture materials using semantic similarity
2.  **Augmentation**: Add the retrieved content to our prompt as context for the AI
3.  **Generation**: Use Claude to generate an answer based on the retrieved information

The `rag_answer()` function below implements this complete pipeline:

-   **Input**: Takes a question and optionally the number of chunks to retrieve
-   **Retrieval Step**: Uses our `search_chunks()` function to find the most relevant sections
-   **Quality Check**: Filters out results with low similarity scores (< 0.2) to avoid irrelevant content
-   **Smart Augmentation**: Combines retrieved chunks but ensures we end at complete sentences (no cut-off mid-sentence)
-   **Prompt Engineering**: Creates a structured prompt that includes both the question and retrieved course materials
-   **Generation**: Sends the augmented prompt to Claude with low temperature (0.0) for factual accuracy
-   **Output**: Returns an answer grounded in our actual course materials

This approach ensures the AI answers questions using specific information from our course materials, rather than just relying on its general training data.

```
<span></span><span>def</span><span> </span><span>rag_answer</span><span>(</span><span>question</span><span>,</span> <span>max_chunks</span><span>=</span><span>2</span><span>):</span>
<span>    </span><span>"""</span>
<span>    Answer a question using RAG (Retrieval Augmented Generation).</span>
<span>    </span>
<span>    Improved version that doesn't cut off mid-sentence!</span>
<span>    </span>
<span>    The three RAG steps:</span>
<span>    1. RETRIEVAL: Find relevant chunks from course materials</span>
<span>    2. AUGMENTATION: Add those chunks to the prompt</span>
<span>    3. GENERATION: Get Claude to answer using the retrieved content</span>
<span>    """</span>
    <span>print</span><span>(</span><span>f</span><span>"Searching for content related to: '</span><span>{</span><span>question</span><span>}</span><span>'"</span><span>)</span>
    
    <span># Step 1: Retrieve relevant chunks</span>
    <span>results</span> <span>=</span> <span>search_chunks</span><span>(</span><span>question</span><span>,</span> <span>top_k</span><span>=</span><span>max_chunks</span><span>)</span>
    
    <span># Check if we found relevant content</span>
    <span>if</span> <span>results</span><span>[</span><span>0</span><span>][</span><span>'similarity'</span><span>]</span> <span>&lt;</span> <span>0.2</span><span>:</span>
        <span>return</span> <span>"No relevant content found in course materials for this question."</span>
    
    <span>print</span><span>(</span><span>f</span><span>"Found </span><span>{</span><span>len</span><span>(</span><span>results</span><span>)</span><span>}</span><span> relevant sections (similarity &gt; 0.2)"</span><span>)</span>
    
    <span># Step 2: Augment - combine retrieved chunks </span>
    <span>context_parts</span> <span>=</span> <span>[]</span>
    <span>for</span> <span>i</span><span>,</span> <span>result</span> <span>in</span> <span>enumerate</span><span>(</span><span>results</span><span>,</span> <span>1</span><span>):</span>
        <span># Take more content but end at a complete sentence</span>
        <span>chunk_text</span> <span>=</span> <span>result</span><span>[</span><span>'chunk'</span><span>][</span><span>'text'</span><span>][:</span><span>1500</span><span>]</span>  <span># Take up to 1500 chars</span>
        
        <span># Find the last period, question mark, or exclamation point</span>
        <span># to end at a complete sentence</span>
        <span>last_sentence_end</span> <span>=</span> <span>max</span><span>(</span>
            <span>chunk_text</span><span>.</span><span>rfind</span><span>(</span><span>'.'</span><span>),</span>
            <span>chunk_text</span><span>.</span><span>rfind</span><span>(</span><span>'?'</span><span>),</span>
            <span>chunk_text</span><span>.</span><span>rfind</span><span>(</span><span>'!'</span><span>)</span>
        <span>)</span>
        
        <span>if</span> <span>last_sentence_end</span> <span>&gt;</span> <span>0</span><span>:</span>
            <span>chunk_text</span> <span>=</span> <span>chunk_text</span><span>[:</span><span>last_sentence_end</span> <span>+</span> <span>1</span><span>]</span>
        
        <span>context_parts</span><span>.</span><span>append</span><span>(</span><span>f</span><span>"Section </span><span>{</span><span>i</span><span>}</span><span>:</span><span>\n</span><span>{</span><span>chunk_text</span><span>}</span><span>"</span><span>)</span>
    
    <span>context</span> <span>=</span> <span>"</span><span>\n\n</span><span>---</span><span>\n\n</span><span>"</span><span>.</span><span>join</span><span>(</span><span>context_parts</span><span>)</span>
    
    <span># Create augmented prompt with retrieved content</span>
    <span>augmented_prompt</span> <span>=</span> <span>f</span><span>"""Based on the following course materials from Lecture 7, answer this question: </span><span>{</span><span>question</span><span>}</span>

<span>COURSE MATERIALS:</span>
<span>{</span><span>context</span><span>}</span>

<span>Please provide a comprehensive answer based specifically on what the course materials say. Use the exact terminology and examples from the lecture."""</span>
    
    <span># Step 3: Generate answer with Claude</span>
    <span>response</span> <span>=</span> <span>client</span><span>.</span><span>messages</span><span>.</span><span>create</span><span>(</span>
        <span>model</span><span>=</span><span>"claude-sonnet-4-20250514"</span><span>,</span>
        <span>max_tokens</span><span>=</span><span>400</span><span>,</span>
        <span>temperature</span><span>=</span><span>0.0</span><span>,</span>  <span># Low temperature for factual accuracy</span>
        <span>messages</span><span>=</span><span>[{</span><span>"role"</span><span>:</span> <span>"user"</span><span>,</span> <span>"content"</span><span>:</span> <span>augmented_prompt</span><span>}]</span>
    <span>)</span>
    
    <span>return</span> <span>response</span><span>.</span><span>content</span><span>[</span><span>0</span><span>]</span><span>.</span><span>text</span>
```

```
<span></span><span># Test RAG answering with a question about course content</span>
<span>test_question</span> <span>=</span> <span>"What are the main parameters for API calls we learned about?"</span>

<span>print</span><span>(</span><span>"="</span> <span>*</span> <span>70</span><span>)</span>
<span>print</span><span>(</span><span>"RAG-POWERED ANSWER"</span><span>)</span>
<span>print</span><span>(</span><span>"="</span> <span>*</span> <span>70</span><span>)</span>
<span>answer</span> <span>=</span> <span>rag_answer</span><span>(</span><span>test_question</span><span>)</span>
<span>print</span><span>(</span><span>f</span><span>"</span><span>\n</span><span>Answer based on Lecture 7 content:"</span><span>)</span>
<span>print</span><span>(</span><span>answer</span><span>)</span>
<span>print</span><span>(</span><span>"="</span> <span>*</span> <span>70</span><span>)</span>
```

```
======================================================================
RAG-POWERED ANSWER
======================================================================
Searching for content related to: 'What are the main parameters for API calls we learned about?'
Found 2 relevant sections (similarity &gt; 0.2)
```

```
Answer based on Lecture 7 content:
Based on the course materials provided, I can see that the lecture covers API fundamentals and mentions that API requests contain parameters, but the specific main parameters for API calls are not fully detailed in the sections you've shared.

From what is included in the course materials, I can identify these parameters that were mentioned:

1. **The prompt/text content** - The text you want the LLM to analyze or process
2. **Model selection** - Which specific model to use for the request
3. **Response length** - How long the response should be

The materials explain that when you want an LLM to analyze text, "you send a specially formatted message over the internet to the LLM's servers. The message contains your prompt, along with parameters like which model to use and how long the response should be."

However, the course materials you've provided appear to be incomplete, as Section 2 (Summary) cuts off mid-sentence when discussing "Best practices for managing API keys using environment files and ." This suggests there may be additional content about API parameters that wasn't included in what you shared.

To provide a more comprehensive answer about the main parameters for API calls that were covered in Lecture 7, I would need access to the complete course materials, particularly any sections that might detail the specific parameter options and their usage.
======================================================================
```

### Comparing RAG vs Non-RAG Responses

Let's see the dramatic difference between Claude's general knowledge and answers grounded in your specific course materials. This demonstrates why RAG is so powerful for working with your own documents:

```
<span></span><span>comparison_question</span> <span>=</span> <span>"What did we learn about conversation histories in the API?"</span>

<span># Without RAG - just Claude's general knowledge</span>
<span>print</span><span>(</span><span>"WITHOUT Course Materials (General Knowledge):"</span><span>)</span>
<span>print</span><span>(</span><span>"="</span> <span>*</span> <span>50</span><span>)</span>
<span>general_response</span> <span>=</span> <span>client</span><span>.</span><span>messages</span><span>.</span><span>create</span><span>(</span>
    <span>model</span><span>=</span><span>"claude-sonnet-4-20250514"</span><span>,</span>
    <span>max_tokens</span><span>=</span><span>200</span><span>,</span>
    <span>messages</span><span>=</span><span>[{</span><span>"role"</span><span>:</span> <span>"user"</span><span>,</span> <span>"content"</span><span>:</span> <span>comparison_question</span><span>}]</span>
<span>)</span>
<span>print</span><span>(</span><span>general_response</span><span>.</span><span>content</span><span>[</span><span>0</span><span>]</span><span>.</span><span>text</span><span>)</span>

<span>print</span><span>(</span><span>"</span><span>\n</span><span>"</span> <span>+</span> <span>"="</span> <span>*</span> <span>70</span> <span>+</span> <span>"</span><span>\n</span><span>"</span><span>)</span>

<span># With RAG - using course materials</span>
<span>print</span><span>(</span><span>"WITH Course Materials (RAG-Enhanced):"</span><span>)</span>
<span>print</span><span>(</span><span>"="</span> <span>*</span> <span>50</span><span>)</span>
<span>rag_answer_text</span> <span>=</span> <span>rag_answer</span><span>(</span><span>comparison_question</span><span>)</span>
<span>print</span><span>(</span><span>rag_answer_text</span><span>)</span>

<span>print</span><span>(</span><span>"</span><span>\n</span><span>"</span> <span>+</span> <span>"="</span> <span>*</span> <span>70</span><span>)</span>
<span>print</span><span>(</span><span>"</span><span>\n</span><span>Notice: The RAG answer references specific details from YOUR lecture!"</span><span>)</span>
<span>print</span><span>(</span><span>"It mentions the exact concepts and examples we covered in class."</span><span>)</span>
```

```
WITHOUT Course Materials (General Knowledge):
==================================================
```

````
I don't have the specific context of which API you're referring to, so I can't give you details about what was covered in a particular lesson or documentation you may have read.

However, I can share some general insights about conversation histories in AI/chat APIs:

**Common patterns include:**
- **Stateless nature**: Most APIs don't maintain conversation history automatically
- **Manual history management**: You typically need to send the full conversation context with each request
- **Message arrays**: Conversations are often structured as arrays of messages with roles (user, assistant, system)
- **Token limits**: Longer histories consume more tokens and may hit API limits
- **Cost implications**: Longer conversation histories increase API costs since you're sending more data

**Typical structure:**
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "

======================================================================

WITH Course Materials (RAG-Enhanced):
==================================================
Searching for content related to: 'What did we learn about conversation histories in the API?'
Found 2 relevant sections (similarity &gt; 0.2)
````

```
Based on the course materials from Lecture 7, here's what we learned about conversation histories in the API:

## Key Learning: The API is Stateless

The most important concept about conversation histories in the API is that **the API is completely stateless**—each API call is independent and has no memory of previous calls. This is fundamentally different from chat interfaces where Claude appears to "remember" your conversation.

## Critical Difference from Chat Interfaces

Unlike the chat interface where Claude seems to "remember" your conversation, when using the API, Claude has no built-in memory between separate API calls. Each request starts with a completely blank slate.

## Maintaining Context Requires Explicit Action

To maintain context across multiple API calls, **you must explicitly provide the entire conversation history with each request**. The API doesn't automatically remember or store previous interactions.

## Practical Demonstration

The course materials provided a clear example showing this concept:

**Call 1:**
- User: "My favorite galaxy is M31. Remember this."
- Claude responds normally

**Call 2 (separate API call):**
- User: "What is my favorite galaxy?"
- Claude has no idea what the user is referring to

As the materials emphasize: "Notice: Claude has no idea! Each API call is completely independent."

## Bottom Line

The key takeaway is that conversation histories don't exist automatically in the API—they must be manually constructed and maintained by including the full conversation context in each API request if you want Claude to have memory of previous exchanges.

======================================================================

Notice: The RAG answer references specific details from YOUR lecture!
It mentions the exact concepts and examples we covered in class.
```

Now for the grand finale—let's combine our calculation functions with document search to create a complete AI assistant. This assistant can both compute astronomical values and search your course materials, choosing the right tool for each question.

This combination is powerful: imagine asking "What's the distance to a star with 0.1 arcsec parallax, and what did we learn about parallax in the course?" The assistant can calculate the distance AND find relevant course content.

### Creating a Search Function for Claude

First, let's wrap our RAG search in a function that Claude can call as a tool. This version properly handles complete sentences:

```
<span></span><span>def</span><span> </span><span>search_course_materials</span><span>(</span><span>question</span><span>,</span> <span>max_results</span><span>=</span><span>2</span><span>):</span>
<span>    </span><span>"""</span>
<span>    Search course materials and return relevant content.</span>
<span>    This function will be callable by Claude as a tool.</span>
<span>    """</span>
    <span># Search for relevant chunks</span>
    <span>results</span> <span>=</span> <span>search_chunks</span><span>(</span><span>question</span><span>,</span> <span>top_k</span><span>=</span><span>max_results</span><span>)</span>
    
    <span># Check if we found anything relevant</span>
    <span>if</span> <span>results</span><span>[</span><span>0</span><span>][</span><span>'similarity'</span><span>]</span> <span>&lt;</span> <span>0.2</span><span>:</span>
        <span>return</span> <span>{</span>
            <span>"status"</span><span>:</span> <span>"no_relevant_content"</span><span>,</span>
            <span>"message"</span><span>:</span> <span>"No relevant course material found for this question"</span>
        <span>}</span>
    
    <span># Format results for Claude</span>
    <span>content_parts</span> <span>=</span> <span>[]</span>
    <span>for</span> <span>i</span><span>,</span> <span>result</span> <span>in</span> <span>enumerate</span><span>(</span><span>results</span><span>,</span> <span>1</span><span>):</span>
        <span># Get section title</span>
        <span>lines</span> <span>=</span> <span>result</span><span>[</span><span>'chunk'</span><span>][</span><span>'text'</span><span>]</span><span>.</span><span>split</span><span>(</span><span>'</span><span>\n</span><span>'</span><span>)</span>
        <span>title</span> <span>=</span> <span>lines</span><span>[</span><span>0</span><span>]</span> <span>if</span> <span>lines</span> <span>else</span> <span>"No title"</span>
        
        <span># Get content ending at complete sentence</span>
        <span>content_text</span> <span>=</span> <span>result</span><span>[</span><span>'chunk'</span><span>][</span><span>'text'</span><span>][:</span><span>1000</span><span>]</span>
        <span>last_period</span> <span>=</span> <span>content_text</span><span>.</span><span>rfind</span><span>(</span><span>'.'</span><span>)</span>
        <span>if</span> <span>last_period</span> <span>&gt;</span> <span>0</span><span>:</span>
            <span>content_text</span> <span>=</span> <span>content_text</span><span>[:</span><span>last_period</span> <span>+</span> <span>1</span><span>]</span>
        
        <span>content_parts</span><span>.</span><span>append</span><span>(</span><span>f</span><span>"Section </span><span>{</span><span>i</span><span>}</span><span> - </span><span>{</span><span>title</span><span>}</span><span>:</span><span>\n</span><span>{</span><span>content_text</span><span>}</span><span>"</span><span>)</span>
    
    <span># Return structured results</span>
    <span>return</span> <span>{</span>
        <span>"status"</span><span>:</span> <span>"found"</span><span>,</span>
        <span>"best_similarity"</span><span>:</span> <span>round</span><span>(</span><span>results</span><span>[</span><span>0</span><span>][</span><span>'similarity'</span><span>],</span> <span>3</span><span>),</span>
        <span>"content"</span><span>:</span> <span>"</span><span>\n\n</span><span>"</span><span>.</span><span>join</span><span>(</span><span>content_parts</span><span>)</span>
    <span>}</span>
```

### Complete Tool Set with Calculations and Search

Now let's create our complete tool set that combines astronomical calculations with course material search:

```
<span></span><span># Complete tools list combining calculations and search</span>
<span>complete_tools</span> <span>=</span> <span>[</span>
    <span>{</span>
        <span>"name"</span><span>:</span> <span>"parallax_to_distance"</span><span>,</span>
        <span>"description"</span><span>:</span> <span>"Calculate stellar distance from parallax measurement"</span><span>,</span>
        <span>"input_schema"</span><span>:</span> <span>{</span>
            <span>"type"</span><span>:</span> <span>"object"</span><span>,</span>
            <span>"properties"</span><span>:</span> <span>{</span>
                <span>"parallax_arcsec"</span><span>:</span> <span>{</span>
                    <span>"type"</span><span>:</span> <span>"number"</span><span>,</span>
                    <span>"description"</span><span>:</span> <span>"Parallax in arcseconds"</span>
                <span>}</span>
            <span>},</span>
            <span>"required"</span><span>:</span> <span>[</span><span>"parallax_arcsec"</span><span>]</span>
        <span>}</span>
    <span>},</span>
    <span>{</span>
        <span>"name"</span><span>:</span> <span>"stellar_luminosity"</span><span>,</span>
        <span>"description"</span><span>:</span> <span>"Calculate stellar luminosity from radius and temperature"</span><span>,</span>
        <span>"input_schema"</span><span>:</span> <span>{</span>
            <span>"type"</span><span>:</span> <span>"object"</span><span>,</span>
            <span>"properties"</span><span>:</span> <span>{</span>
                <span>"radius_solar"</span><span>:</span> <span>{</span>
                    <span>"type"</span><span>:</span> <span>"number"</span><span>,</span>
                    <span>"description"</span><span>:</span> <span>"Radius in solar radii"</span>
                <span>},</span>
                <span>"temperature_k"</span><span>:</span> <span>{</span>
                    <span>"type"</span><span>:</span> <span>"number"</span><span>,</span>
                    <span>"description"</span><span>:</span> <span>"Temperature in Kelvin"</span>
                <span>}</span>
            <span>},</span>
            <span>"required"</span><span>:</span> <span>[</span><span>"radius_solar"</span><span>,</span> <span>"temperature_k"</span><span>]</span>
        <span>}</span>
    <span>},</span>
    <span>{</span>
        <span>"name"</span><span>:</span> <span>"search_course_materials"</span><span>,</span>
        <span>"description"</span><span>:</span> <span>"Search Lecture 7 notes for relevant course content"</span><span>,</span>
        <span>"input_schema"</span><span>:</span> <span>{</span>
            <span>"type"</span><span>:</span> <span>"object"</span><span>,</span>
            <span>"properties"</span><span>:</span> <span>{</span>
                <span>"question"</span><span>:</span> <span>{</span>
                    <span>"type"</span><span>:</span> <span>"string"</span><span>,</span>
                    <span>"description"</span><span>:</span> <span>"Topic or question to search for"</span>
                <span>},</span>
                <span>"max_results"</span><span>:</span> <span>{</span>
                    <span>"type"</span><span>:</span> <span>"integer"</span><span>,</span>
                    <span>"description"</span><span>:</span> <span>"Maximum number of results (default 2)"</span><span>,</span>
                    <span>"default"</span><span>:</span> <span>2</span>
                <span>}</span>
            <span>},</span>
            <span>"required"</span><span>:</span> <span>[</span><span>"question"</span><span>]</span>
        <span>}</span>
    <span>}</span>
<span>]</span>

<span>print</span><span>(</span><span>f</span><span>"Complete AI Assistant with </span><span>{</span><span>len</span><span>(</span><span>complete_tools</span><span>)</span><span>}</span><span> capabilities:"</span><span>)</span>
<span>for</span> <span>tool</span> <span>in</span> <span>complete_tools</span><span>:</span>
    <span>print</span><span>(</span><span>f</span><span>"  • </span><span>{</span><span>tool</span><span>[</span><span>'name'</span><span>]</span><span>}</span><span>: </span><span>{</span><span>tool</span><span>[</span><span>'description'</span><span>]</span><span>}</span><span>"</span><span>)</span>
```

```
Complete AI Assistant with 3 capabilities:
  • parallax_to_distance: Calculate stellar distance from parallax measurement
  • stellar_luminosity: Calculate stellar luminosity from radius and temperature
  • search_course_materials: Search Lecture 7 notes for relevant course content
```

### Complete Assistant Function with Natural Language Responses

Let's create a complete assistant function that handles the entire workflow, ensuring we always get natural language answers whether Claude uses calculations or searches:

```
<span></span><span>def</span><span> </span><span>complete_assistant</span><span>(</span><span>question</span><span>):</span>
<span>    </span><span>"""</span>
<span>    Complete AI assistant that can calculate and search.</span>
<span>    Always returns a natural language answer.</span>
<span>    """</span>
    <span>print</span><span>(</span><span>f</span><span>"Processing: </span><span>{</span><span>question</span><span>}</span><span>"</span><span>)</span>

    <span># Get Claude's initial response</span>
    <span>initial_response</span> <span>=</span> <span>client</span><span>.</span><span>messages</span><span>.</span><span>create</span><span>(</span>
        <span>model</span><span>=</span><span>"claude-sonnet-4-20250514"</span><span>,</span>
        <span>max_tokens</span><span>=</span><span>300</span><span>,</span>
        <span>tools</span><span>=</span><span>complete_tools</span><span>,</span>
        <span>messages</span><span>=</span><span>[{</span><span>"role"</span><span>:</span> <span>"user"</span><span>,</span> <span>"content"</span><span>:</span> <span>question</span><span>}]</span>
    <span>)</span>

    <span># Check if Claude needs a tool</span>
    <span>if</span> <span>initial_response</span><span>.</span><span>stop_reason</span> <span>!=</span> <span>"tool_use"</span><span>:</span>
        <span># Some SDKs return plain dicts when running offline; fall back to repr</span>
        <span># repr() returns a string representation of the object for debugging</span>
        <span>text_blocks</span> <span>=</span> <span>[</span>
            <span>getattr</span><span>(</span><span>block</span><span>,</span> <span>"text"</span><span>,</span> <span>None</span><span>)</span>
            <span>if</span> <span>not</span> <span>isinstance</span><span>(</span><span>block</span><span>,</span> <span>dict</span><span>)</span>
            <span>else</span> <span>block</span><span>.</span><span>get</span><span>(</span><span>"text"</span><span>)</span>
            <span>for</span> <span>block</span> <span>in</span> <span>getattr</span><span>(</span><span>initial_response</span><span>,</span> <span>"content"</span><span>,</span> <span>[])</span>
        <span>]</span>
        <span>text_blocks</span> <span>=</span> <span>[</span><span>item</span> <span>for</span> <span>item</span> <span>in</span> <span>text_blocks</span> <span>if</span> <span>item</span><span>]</span>
        <span>return</span> <span>""</span><span>.</span><span>join</span><span>(</span><span>text_blocks</span><span>)</span><span>.</span><span>strip</span><span>()</span> <span>or</span> <span>repr</span><span>(</span><span>initial_response</span><span>)</span>

    <span># Execute the requested tool</span>
    <span>tool_use</span> <span>=</span> <span>initial_response</span><span>.</span><span>content</span><span>[</span><span>-</span><span>1</span><span>]</span>
    <span>print</span><span>(</span><span>f</span><span>"  → Using tool: </span><span>{</span><span>tool_use</span><span>.</span><span>name</span><span>}</span><span>"</span><span>)</span>

    <span># Execute the appropriate function</span>
    <span>if</span> <span>tool_use</span><span>.</span><span>name</span> <span>==</span> <span>"parallax_to_distance"</span><span>:</span>
        <span>result</span> <span>=</span> <span>parallax_to_distance</span><span>(</span><span>tool_use</span><span>.</span><span>input</span><span>[</span><span>'parallax_arcsec'</span><span>])</span>
    <span>elif</span> <span>tool_use</span><span>.</span><span>name</span> <span>==</span> <span>"stellar_luminosity"</span><span>:</span>
        <span>result</span> <span>=</span> <span>stellar_luminosity</span><span>(</span>
            <span>tool_use</span><span>.</span><span>input</span><span>[</span><span>'radius_solar'</span><span>],</span>
            <span>tool_use</span><span>.</span><span>input</span><span>[</span><span>'temperature_k'</span><span>]</span>
        <span>)</span>
    <span>elif</span> <span>tool_use</span><span>.</span><span>name</span> <span>==</span> <span>"search_course_materials"</span><span>:</span>
        <span>result</span> <span>=</span> <span>search_course_materials</span><span>(</span>
            <span>tool_use</span><span>.</span><span>input</span><span>[</span><span>'question'</span><span>],</span>
            <span>tool_use</span><span>.</span><span>input</span><span>.</span><span>get</span><span>(</span><span>'max_results'</span><span>,</span> <span>2</span><span>)</span>
        <span>)</span>
    <span>else</span><span>:</span>
        <span>result</span> <span>=</span> <span>{</span><span>"error"</span><span>:</span> <span>f</span><span>"Unknown function: </span><span>{</span><span>tool_use</span><span>.</span><span>name</span><span>}</span><span>"</span><span>}</span>

    <span># Get natural language response</span>
    <span>final_response</span> <span>=</span> <span>client</span><span>.</span><span>messages</span><span>.</span><span>create</span><span>(</span>
        <span>model</span><span>=</span><span>"claude-sonnet-4-20250514"</span><span>,</span>
        <span>max_tokens</span><span>=</span><span>400</span><span>,</span>
        <span>tools</span><span>=</span><span>complete_tools</span><span>,</span>
        <span>messages</span><span>=</span><span>[</span>
            <span>{</span><span>"role"</span><span>:</span> <span>"user"</span><span>,</span> <span>"content"</span><span>:</span> <span>question</span><span>},</span>
            <span>{</span><span>"role"</span><span>:</span> <span>"assistant"</span><span>,</span> <span>"content"</span><span>:</span> <span>initial_response</span><span>.</span><span>content</span><span>},</span>
            <span>{</span>
                <span>"role"</span><span>:</span> <span>"user"</span><span>,</span>
                <span>"content"</span><span>:</span> <span>[{</span>
                    <span>"type"</span><span>:</span> <span>"tool_result"</span><span>,</span>
                    <span>"tool_use_id"</span><span>:</span> <span>tool_use</span><span>.</span><span>id</span><span>,</span>
                    <span>"content"</span><span>:</span> <span>str</span><span>(</span><span>result</span><span>)</span>
                <span>}]</span>
            <span>}</span>
        <span>]</span>
    <span>)</span>

    <span>text_blocks</span> <span>=</span> <span>[</span>
        <span>getattr</span><span>(</span><span>block</span><span>,</span> <span>"text"</span><span>,</span> <span>None</span><span>)</span>
        <span>if</span> <span>not</span> <span>isinstance</span><span>(</span><span>block</span><span>,</span> <span>dict</span><span>)</span>
        <span>else</span> <span>block</span><span>.</span><span>get</span><span>(</span><span>"text"</span><span>)</span>
        <span>for</span> <span>block</span> <span>in</span> <span>getattr</span><span>(</span><span>final_response</span><span>,</span> <span>"content"</span><span>,</span> <span>[])</span>
    <span>]</span>
    <span>text_blocks</span> <span>=</span> <span>[</span><span>item</span> <span>for</span> <span>item</span> <span>in</span> <span>text_blocks</span> <span>if</span> <span>item</span><span>]</span>
    <span>if</span> <span>text_blocks</span><span>:</span>
        <span>return</span> <span>""</span><span>.</span><span>join</span><span>(</span><span>text_blocks</span><span>)</span><span>.</span><span>strip</span><span>()</span>

    <span># As a fallback, provide the raw response so readers know to run locally</span>
    <span>return</span> <span>repr</span><span>(</span><span>final_response</span><span>)</span>
```

### Testing the Complete System

Let's test our complete AI assistant with different types of questions—calculations, course content searches, and general questions. Notice how Claude automatically chooses the right tool and provides natural language answers:

```
<span></span><span># Test different types of questions</span>
<span>test_scenarios</span> <span>=</span> <span>[</span>
    <span>"What's the distance to a star with 0.1 arcsecond parallax?"</span><span>,</span>
    <span>"What did we learn about conversation histories in the API?"</span><span>,</span>
    <span>"Calculate the luminosity of a star with radius 3 solar radii and temperature 7000K"</span>
<span>]</span>

<span>for</span> <span>i</span><span>,</span> <span>question</span> <span>in</span> <span>enumerate</span><span>(</span><span>test_scenarios</span><span>,</span> <span>1</span><span>):</span>
    <span>print</span><span>(</span><span>f</span><span>"</span><span>\n</span><span>Test </span><span>{</span><span>i</span><span>}</span><span>:"</span><span>)</span>
    <span>print</span><span>(</span><span>"="</span> <span>*</span> <span>60</span><span>)</span>
    <span>answer</span> <span>=</span> <span>complete_assistant</span><span>(</span><span>question</span><span>)</span>
    <span>print</span><span>(</span><span>f</span><span>"</span><span>\n</span><span>Answer: </span><span>{</span><span>answer</span><span>}</span><span>"</span><span>)</span>
    <span>print</span><span>(</span><span>"="</span> <span>*</span> <span>60</span><span>)</span>
```

```
Test 1:
============================================================
Processing: What's the distance to a star with 0.1 arcsecond parallax?
```

```
  → Using tool: parallax_to_distance
```

```
Answer: The distance to a star with a parallax of 0.1 arcseconds is **10 parsecs**.

This follows the parallax-distance relationship where distance (in parsecs) = 1 / parallax (in arcseconds). So with a parallax of 0.1 arcseconds, the distance is 1/0.1 = 10 parsecs.

To put this in perspective:
- 10 parsecs = approximately 32.6 light-years
- This is a relatively nearby star in our local stellar neighborhood
============================================================

Test 2:
============================================================
Processing: What did we learn about conversation histories in the API?
```

```
  → Using tool: search_course_materials
```

```
Answer: Message(id='msg_019ucpMesbGmBWn4rwbNjFp8', content=[ToolUseBlock(id='toolu_01C1CMQQ1ynLnXuQe6hsoeyw', input={'question': 'conversation history context API calls'}, name='search_course_materials', type='tool_use')], model='claude-sonnet-4-20250514', role='assistant', stop_reason='tool_use', stop_sequence=None, type='message', usage=Usage(cache_creation=CacheCreation(ephemeral_1h_input_tokens=0, ephemeral_5m_input_tokens=0), cache_creation_input_tokens=0, cache_read_input_tokens=0, input_tokens=1065, output_tokens=59, server_tool_use=None, service_tier='standard'))
============================================================

Test 3:
============================================================
Processing: Calculate the luminosity of a star with radius 3 solar radii and temperature 7000K
```

```
  → Using tool: stellar_luminosity
```

```
Answer: The star with a radius of 3 solar radii and temperature of 7000K has:

- **Luminosity: 19.5 solar luminosities** (L☉)
- **Luminosity: 7.46 × 10²⁷ watts**

This means the star is about 19.5 times more luminous than our Sun. The higher luminosity comes from both the larger radius (3 times the Sun's radius) and the higher temperature (7000K compared to the Sun's ~5778K), with luminosity scaling as R² × T⁴ according to the Stefan-Boltzmann law.
============================================================
```

## Vector Databases - The Professional Solution

What we've built today is a fully functional RAG system that works well for single documents or small collections. However, when you're dealing with thousands of documents or millions of chunks in professional research, you need more sophisticated tools called **vector databases**.

Vector databases are specialized systems designed to store and search embeddings efficiently. They're like regular databases, but optimized for finding similar vectors quickly, even when you have billions of them.

### Three Popular Vector Database Solutions

Here are three of the most popular vector database solutions you're likely to encounter:

**1\. Chroma** - Perfect for getting started Chroma is an open-source, completely free vector database that works seamlessly with Python. It can run entirely in memory for small projects, making it ideal for prototyping and learning. The API feels natural after today's lecture—you'll find the transition straightforward.

**2\. Pinecone** - The managed cloud solution Pinecone offers a fully managed cloud service where you don't need to maintain any servers. It handles scaling automatically as your data grows, making it more expensive but very reliable and fast. Many production AI applications use Pinecone when they need enterprise-level reliability without the hassle of infrastructure management.

**3\. FAISS** - Facebook's high-performance library Developed by Facebook AI Research, FAISS is extremely fast, especially with GPU acceleration. It's more of a library than a full database, but when speed is absolutely critical and you need to handle billions of vectors efficiently, FAISS is often the go-to choice.

### When to Use Vector Databases

Our implementation today works great for single documents or small collections (under 100 documents), prototyping and learning RAG concepts, and understanding how semantic search works under the hood.

You should consider upgrading to a vector database when you're working with thousands of documents or research papers, need persistent storage with embeddings saved to disk, have multiple users searching simultaneously, want advanced features like filtering and metadata search, or are building production applications for research teams.

### Working Example: ChromaDB

Let's see how easy it is to upgrade our system to use ChromaDB. ChromaDB is a vector database that handles storage and search for us, though there are a few important differences from our manual implementation:

**Key Differences to Note:**

1.  **ChromaDB uses its own default embedding model** (not our `all-MiniLM-L6-v2`) unless you explicitly override it
2.  **ChromaDB returns distances, not similarities** - lower values mean more similar

Here's the implementation:

First, install ChromaDB:

Then, import ChromaDB:

```
<span></span><span>import</span><span> </span><span>chromadb</span>

<span># Read the same Lecture 7 file</span>
<span>with</span> <span>open</span><span>(</span><span>'Lecture7_LLM_API_Basics_20250924.md'</span><span>,</span> <span>'r'</span><span>)</span> <span>as</span> <span>f</span><span>:</span>
    <span>lecture7_content</span> <span>=</span> <span>f</span><span>.</span><span>read</span><span>()</span>

<span># Use our same chunking function</span>
<span>lecture_chunks</span> <span>=</span> <span>chunk_by_sections</span><span>(</span><span>lecture7_content</span><span>)</span>

<span># Create ChromaDB client and clean up any existing collection</span>
<span>chroma_client</span> <span>=</span> <span>chromadb</span><span>.</span><span>Client</span><span>()</span>

<span># Delete the collection if it already exists</span>
<span>try</span><span>:</span>
    <span>chroma_client</span><span>.</span><span>delete_collection</span><span>(</span><span>name</span><span>=</span><span>"lecture7_rag"</span><span>)</span>
    <span>print</span><span>(</span><span>"Deleted existing collection"</span><span>)</span>
<span>except</span><span>:</span>
    <span>print</span><span>(</span><span>"No existing collection to delete"</span><span>)</span>

<span># Create new collection</span>
<span>collection</span> <span>=</span> <span>chroma_client</span><span>.</span><span>create_collection</span><span>(</span>
    <span>name</span><span>=</span><span>"lecture7_rag"</span><span>,</span>
    <span>metadata</span><span>=</span><span>{</span><span>"description"</span><span>:</span> <span>"Lecture 7 content for RAG"</span><span>}</span>
<span>)</span>

<span># Add all chunks to ChromaDB (it handles embeddings automatically!)</span>
<span>for</span> <span>i</span><span>,</span> <span>chunk</span> <span>in</span> <span>enumerate</span><span>(</span><span>lecture_chunks</span><span>):</span>
    <span>collection</span><span>.</span><span>add</span><span>(</span>
        <span>documents</span><span>=</span><span>[</span><span>chunk</span><span>[</span><span>'text'</span><span>]],</span>
        <span>ids</span><span>=</span><span>[</span><span>f</span><span>"chunk_</span><span>{</span><span>i</span><span>}</span><span>"</span><span>],</span>
        <span>metadatas</span><span>=</span><span>[{</span><span>"chunk_id"</span><span>:</span> <span>i</span><span>,</span> <span>"length"</span><span>:</span> <span>chunk</span><span>[</span><span>'length'</span><span>]}]</span>
    <span>)</span>

<span>print</span><span>(</span><span>f</span><span>"Added </span><span>{</span><span>len</span><span>(</span><span>lecture_chunks</span><span>)</span><span>}</span><span> chunks to ChromaDB"</span><span>)</span>

<span># Now search is incredibly simple</span>
<span>results</span> <span>=</span> <span>collection</span><span>.</span><span>query</span><span>(</span>
    <span>query_texts</span><span>=</span><span>[</span><span>"How do I keep API keys secure?"</span><span>],</span>
    <span>n_results</span><span>=</span><span>2</span>
<span>)</span>

<span># Display results</span>
<span>for</span> <span>i</span><span>,</span> <span>(</span><span>doc</span><span>,</span> <span>distance</span><span>)</span> <span>in</span> <span>enumerate</span><span>(</span><span>zip</span><span>(</span><span>results</span><span>[</span><span>'documents'</span><span>][</span><span>0</span><span>],</span> <span>results</span><span>[</span><span>'distances'</span><span>][</span><span>0</span><span>])):</span>
    <span>print</span><span>(</span><span>f</span><span>"</span><span>\n</span><span>Result </span><span>{</span><span>i</span><span>+</span><span>1</span><span>}</span><span> (distance: </span><span>{</span><span>distance</span><span>:</span><span>.3f</span><span>}</span><span>):"</span><span>)</span>
    <span>print</span><span>(</span><span>doc</span><span>[:</span><span>200</span><span>]</span> <span>+</span> <span>"..."</span><span>)</span>
```

```
No existing collection to delete
```

```
Added 12 chunks to ChromaDB

Result 1 (distance: 1.189):
## Summary

### Key Concepts
In this lecture, you've learned:
- **API Fundamentals**: How to communicate with Large Language Models programmatically through structured requests and responses, transfor...

Result 2 (distance: 1.300):
## Understanding APIs

Let's demystify this term that gets thrown around constantly in programming. API stands for Application Programming Interface, but that definition helps nobody. Here's a better ...
```

That's it! Notice how ChromaDB:

-   Automatically creates embeddings using the same model
-   Stores everything persistently (survives restarts)
-   Handles all the vector similarity calculations
-   Returns results ranked by relevance
-   Can store metadata alongside each chunk

The concepts are identical to what we built—ChromaDB just handles the infrastructure for us. You could now search through hundreds of lecture files without changing the code!

What matters isn't the specific vector database you use, but understanding the concepts we've covered today. Documents get chunked into manageable pieces, chunks get converted to embeddings, queries get converted to embeddings, similarity search finds relevant chunks, and retrieved content augments LLM prompts. With this understanding, you can use any vector database—they're all just different implementations of the same core ideas you've mastered today!

## Summary

### Key Concepts

In this lecture, you've learned:

-   **Function Tools**: How to transform Python functions into tools that LLMs can call automatically, creating a bridge between natural language requests and computational execution
-   **Function Schemas**: The structured format for describing functions to LLMs, enabling them to understand when and how to use your calculations
-   **Document Processing and Chunking**: Strategies for breaking large documents into searchable pieces while preserving context and meaning
-   **Embeddings and Semantic Search**: How text gets converted to numerical vectors that capture meaning, enabling similarity-based retrieval even when exact words don't match
-   **RAG Implementation**: The complete retrieval-augmented generation pipeline that grounds LLM responses in your specific documents rather than general knowledge
-   **Tool Integration**: Combining computational functions with document search to create an AI assistant that can both calculate and retrieve information
-   **Vector Databases**: Professional solutions for scaling RAG systems to thousands of documents while maintaining fast search performance

### What You Can Now Do

After working through this material, you should be able to:

-   Convert any Python function into an LLM-callable tool with proper schemas and error handling
-   Build RAG systems that search through your course materials or research papers to provide grounded, accurate answers
-   Create AI assistants that seamlessly combine calculations with document retrieval based on user questions
-   Process and chunk documents effectively, balancing context preservation with search efficiency
-   Implement semantic search using embeddings and cosine similarity for meaning-based retrieval
-   Understand when to upgrade from custom implementations to professional vector databases
-   Debug and optimize the complete workflow from function definition to natural language response

### Practice Suggestions

To solidify these concepts:

1.  Create additional astronomical calculation functions (orbital mechanics, redshift calculations) and add them to your tool set
2.  Convert all your lecture notebooks to markdown and build a searchable knowledge base for the entire course
3.  Experiment with different chunking strategies (overlapping chunks, smaller/larger sizes) to see how they affect search quality
4.  Try different embedding models and compare their performance on astronomical terminology
5.  Build a specialized assistant for your research project that combines domain-specific calculations with literature search

### Looking Ahead

Next week in Lecture 9, we'll explore GitHub and professional coding development. The systems you've built today—function tools and RAG implementations—are exactly the kind of projects you'll want to showcase in your GitHub portfolio. You'll learn how to version control your AI assistants, collaborate with others on these tools, and deploy them for others to use. The combination of today's AI capabilities with next week's professional development practices will prepare you to build and share powerful research tools that can accelerate astronomical discovery.
