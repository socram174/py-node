import { execSync } from 'child_process';
import express from 'express';


const PORT = process.env.PORT || 3000;
const app = express();

app.get('/', (req, res) => {
    const result = execSync('python main.py', { encoding: 'utf-8' });
    res.send(result);
});

app.listen(PORT, () => {
    console.log('Server is running on http://localhost:3000');
});