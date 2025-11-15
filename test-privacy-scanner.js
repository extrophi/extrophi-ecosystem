// Quick test of privacy scanner patterns
// Run with: node test-privacy-scanner.js

// Simulating the scanner (Node.js version)
const patterns = [
  { name: 'SSN', regex: /\b\d{3}-\d{2}-\d{4}\b/g, severity: 'danger' },
  { name: 'Credit Card', regex: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, severity: 'danger' },
  { name: 'Email', regex: /\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b/g, severity: 'caution' },
  { name: 'Phone Number', regex: /(?<!\d)\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b/g, severity: 'caution' },
  { name: 'Street Address', regex: /\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b/g, severity: 'caution' },
  { name: 'Account Number', regex: /\bAccount\s*#?\s*\d{8,}\b/gi, severity: 'danger' },
  { name: 'Passport Number', regex: /\b[A-Z]{1,2}\d{6,9}\b/g, severity: 'danger' },
  { name: 'IP Address', regex: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g, severity: 'caution' }
];

function scanText(text) {
  const matches = [];
  patterns.forEach(pattern => {
    pattern.regex.lastIndex = 0;
    let match;
    while ((match = pattern.regex.exec(text)) !== null) {
      matches.push({
        type: pattern.name,
        value: match[0],
        start: match.index,
        end: match.index + match[0].length,
        severity: pattern.severity
      });
    }
  });
  matches.sort((a, b) => a.start - b.start);
  return matches;
}

// Test samples
const testText = `
Here's my test data:
1. SSN: 123-45-6789
2. Credit Card: 4532-1234-5678-9010
3. Email: john.doe@example.com
4. Phone: (555) 123-4567 or 555-123-4567
5. Address: 123 Main Street, 456 Oak Avenue
6. Account: Account #12345678901
7. Passport: A1234567
8. IP: 192.168.1.1

Also testing without spaces:
Credit card: 4532123456789010

Regular text should not match: hello world, test123, 5551234567 (no separators).
`;

console.log('Testing Privacy Scanner\n' + '='.repeat(50));
console.log('Test Text:', testText);
console.log('\n' + '='.repeat(50));
console.log('Detected Matches:\n');

const matches = scanText(testText);

if (matches.length === 0) {
  console.log('No matches found!');
} else {
  const dangerMatches = matches.filter(m => m.severity === 'danger');
  const cautionMatches = matches.filter(m => m.severity === 'caution');

  console.log(`Total matches: ${matches.length}`);
  console.log(`Danger: ${dangerMatches.length}, Caution: ${cautionMatches.length}\n`);

  if (dangerMatches.length > 0) {
    console.log('DANGER MATCHES:');
    dangerMatches.forEach((m, i) => {
      console.log(`  ${i + 1}. ${m.type}: "${m.value}"`);
    });
    console.log();
  }

  if (cautionMatches.length > 0) {
    console.log('CAUTION MATCHES:');
    cautionMatches.forEach((m, i) => {
      console.log(`  ${i + 1}. ${m.type}: "${m.value}"`);
    });
  }
}

console.log('\n' + '='.repeat(50));
console.log('Test Complete!');
