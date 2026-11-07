const fs = require('fs');

// Read drawio XML
const drawioXml = fs.readFileSync('CLASS_DIAGRAM_PIXELT_FINAL_INDEPENDENT_AUDIT.drawio', 'utf8');

// Debug edge regex
const edgeCellRegex = /<mxCell id="([^"]+)" style="([^"]*)" edge="1" parent="1" source="([^"]+)" target="([^"]+)">/g;
const edgeMatches = [];

let m;
while ((m = edgeCellRegex.exec(drawioXml)) !== null) {
  edgeMatches.push(m);
  console.log('Edge found:', m[1], 'source:', m[3], 'target:', m[4]);
}

console.log('Total edges:', edgeMatches.length);

// Debug multiplicity regex
const multRegex = /<mxCell id="([^"]+)" value="([^"]*)" style="[^"]*" vertex="1" parent="1">[\s\S]*?<mxGeometry x="([\d.]+)" y="([\d.]+)" width="[\d.]+" height="[\d.]+" as="geometry"\/><\/mxCell>/g;
const multLabels = new Map();

while ((m = multRegex.exec(drawioXml)) !== null) {
  const id = m[1];
  const value = m[2];
  const x = parseFloat(m[3]);
  const y = parseFloat(m[4]);
  console.log('Mult found:', id, 'value:', value, 'x:', x, 'y:', y);
  if (value === '1' || value === '*' || value === '0..1') {
    multLabels.set(id, { value, x, y });
  }
}

console.log('Total mult labels:', multLabels.size);

// Show first 500 chars of drawio for debugging
console.log('\nFirst 500 chars of drawio:');
console.log(drawioXml.substring(0, 500));