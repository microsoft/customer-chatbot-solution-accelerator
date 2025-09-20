const express = require('express');
const path = require('path');
const app = express();
const port = process.env.PORT || 80;

// Serve static files from current directory
app.use(express.static(__dirname));

// Handle React Router (send all routes to index.html)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(port, '0.0.0.0', () => {
  console.log(Server running on port );
});
