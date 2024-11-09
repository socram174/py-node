import { execSync } from 'child_process';



const result = execSync('python main.py', { encoding: 'utf-8' });

console.log("NODE: " + result);