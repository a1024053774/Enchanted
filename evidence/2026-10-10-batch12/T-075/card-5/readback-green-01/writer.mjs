import { DatabaseSync } from 'node:sqlite';
const db = new DatabaseSync(process.argv[2]);
db.exec("PRAGMA journal_mode=WAL; CREATE TABLE independent_values(id INTEGER,value TEXT); INSERT INTO independent_values VALUES(7,'snapshot survives cleanup');");
process.stdout.write('ready\n');
process.stdin.once('data', () => { db.close(); process.exit(0); });
