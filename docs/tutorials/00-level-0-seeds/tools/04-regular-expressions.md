# Tutorial Outline: Regular Expressions

**Category**: Tools
**Level**: 0 (Seed)
**Estimated Time**: 6-8 hours

## Learning Objectives

- Understand regex syntax and pattern matching concepts
- Write regular expressions for common text processing tasks
- Debug and test regex patterns effectively
- Use regex across different tools and languages
- Recognize when regex is (and isn't) the right tool

## Section 1: Regex Fundamentals

**Concepts**:
- What are regular expressions
- Literal characters vs metacharacters
- Regex engines and flavors (PCRE, JavaScript, POSIX)
- Use cases: validation, extraction, transformation

**Skills**:
- Match literal text patterns
- Understand regex use cases
- Choose appropriate regex flavor

## Section 2: Character Classes and Quantifiers

**Concepts**:
- Character classes: [abc], [a-z], [^abc]
- Predefined classes: \d, \w, \s, .
- Quantifiers: *, +, ?, {n}, {n,m}
- Greedy vs lazy matching

**Skills**:
- Match character ranges and sets
- Use quantifiers for repetition
- Control greedy vs lazy behavior

## Section 3: Anchors and Boundaries

**Concepts**:
- Start and end anchors: ^, $
- Word boundaries: \b, \B
- Line vs string anchoring
- Multiline mode

**Skills**:
- Anchor patterns to positions
- Match whole words vs partial
- Handle multiline text

## Section 4: Groups and Capturing

**Concepts**:
- Capturing groups: (pattern)
- Non-capturing groups: (?:pattern)
- Backreferences: \1, \2
- Named groups: (?<name>pattern)

**Skills**:
- Extract data with capturing groups
- Use backreferences for matching
- Work with named groups for clarity

## Section 5: Alternation and Special Constructs

**Concepts**:
- Alternation with pipe: |
- Lookahead: (?=...), (?!...)
- Lookbehind: (?<=...), (?<!...)
- Atomic groups and possessive quantifiers

**Skills**:
- Match alternative patterns
- Use lookahead for conditional matching
- Apply lookbehind where supported

## Section 6: Practical Applications

**Concepts**:
- Email and URL validation
- Phone number formatting
- Date parsing and validation
- Log file parsing

**Skills**:
- Validate common data formats
- Extract structured data
- Parse and transform text

## Section 7: Regex in Different Contexts

**Concepts**:
- Command line: grep, sed, awk
- Programming: JavaScript, Python, Go
- Editors: Vim, VS Code, Sublime
- Tools: regex101, RegExr

**Skills**:
- Use regex in grep and sed
- Apply regex in Python (re module)
- Test regex with online tools

## Section 8: Best Practices and Pitfalls

**Concepts**:
- Readability vs brevity
- Performance considerations
- When NOT to use regex
- Common mistakes and edge cases

**Skills**:
- Write maintainable regex patterns
- Debug complex patterns
- Recognize regex limitations

## Capstone Project

**Log Parser and Analysis Tool**

Build regex-based log analysis system:

1. **Log Parsing**:
   - Parse Apache/Nginx access logs
   - Extract: IP, timestamp, method, URL, status, size
   - Handle various log formats with regex variants
   - Validate log line format

2. **Data Extraction**:
   - Extract error patterns from application logs
   - Parse timestamps across different formats
   - Identify and extract stack traces
   - Extract API endpoints and parameters

3. **Validation Tool**:
   - Email address validator
   - Phone number normalizer (multiple formats)
   - URL validator and component extractor
   - Credit card number validator (Luhn algorithm)

4. **Text Transformation**:
   - Redact sensitive information (SSN, credit cards)
   - Format phone numbers consistently
   - Convert between date formats
   - Normalize whitespace and formatting

5. **Regex Library**:
   - Documented collection of useful patterns
   - Test suite for each pattern
   - Examples for each use case
   - Performance notes

**Deliverables**:
- Python/JavaScript log parser script
- Validation library with 10+ patterns
- Test suite with edge cases
- Documentation with regex explanations
- Interactive demo showing pattern matches

## Prerequisites

- Basic programming knowledge
- Text editor familiarity
- Understanding of strings and text processing
- Terminal basics for testing with grep/sed

## Next Steps

After completing this tutorial, you should be ready for:
- **Advanced Regex**: Recursive patterns, balancing groups
- **Parsing Theory**: When to use parsers instead of regex
- **Text Processing Deep Dive**: sed, awk, Perl mastery
- **Domain-Specific Patterns**: Language-specific parsing
- **Performance Optimization**: Regex efficiency
- **Formal Language Theory**: DFA, NFA, regex compilation

## Resources

- Regular-Expressions.info (comprehensive guide)
- regex101.com (interactive testing)
- RegExr (visual regex builder)
- Mastering Regular Expressions by Jeffrey Friedl
- RegexOne (interactive tutorial)
- Regex Golf (practice challenges)

## Assessment Criteria

Students should be able to:
- [ ] Write regex for common patterns (email, phone, URL)
- [ ] Use character classes and quantifiers correctly
- [ ] Capture and extract data with groups
- [ ] Debug regex patterns using online tools
- [ ] Apply regex in multiple contexts (CLI, code, editor)
- [ ] Explain greedy vs lazy matching
- [ ] Complete capstone with working parsers and validators
