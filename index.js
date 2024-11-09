import { execSync } from 'child_process';
import express from 'express';

const app = express();

app.get('/', (req, res) => {
    const result = execSync('python main.py', { encoding: 'utf-8' });
    res.send(result);
});

app.listen(3000, () => {
    console.log('Server is running on http://localhost:3000');
});