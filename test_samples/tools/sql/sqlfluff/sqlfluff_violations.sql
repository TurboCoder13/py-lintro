-- Sample SQL file with intentional violations for SQLFluff testing
-- This file contains common SQL linting issues

-- L010: Keywords must be upper case (using lowercase select, from, where)
select id, name from users where id = 1;

-- L011: Implicit/explicit aliasing of table (missing AS keyword)
SELECT u.id, u.name FROM users u;

-- L014: Unquoted identifiers should be consistent
SELECT ID, Name, EMAIL FROM users;

-- L019: Leading/trailing whitespace
SELECT id FROM users    ;

-- L036: Select targets should be on new lines (all on one line)
SELECT id, name, email, created_at, updated_at FROM users WHERE active = 1;

-- L044: Query produces an unknown number of result columns (SELECT *)
SELECT * FROM users;

-- Multiple issues in one query
select u.id,u.name,u.email from users u where u.active=1 and u.id>0;
