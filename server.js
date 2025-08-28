const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const { dialogflowWebhook } = require('./index');

const app = express();
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Health check endpoint
app.get('/', (req, res) => {
    res.send('Solar Webhook Server is running!');
});

// Webhook endpoint with proper headers
app.post('/webhook', (req, res) => {
    // Add required headers for Dialogflow
    req.headers['content-type'] = 'application/json';
    req.headers['user-agent'] = 'dialogflow-webhook';
    
    dialogflowWebhook(req, res);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});