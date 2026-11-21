USE campus_auth;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  display_name VARCHAR(100) NOT NULL,
  password_hash VARCHAR(100) NOT NULL,
  is_platform_admin BOOLEAN NOT NULL DEFAULT FALSE,
  student_id INT NULL,
  faculty_id INT NULL,
  dept_id INT NULL,
  INDEX idx_users_student (student_id),
  INDEX idx_users_faculty (faculty_id)
);

CREATE TABLE roles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(30) NOT NULL UNIQUE,
  description VARCHAR(255) NOT NULL DEFAULT ''
);

CREATE TABLE user_roles (
  user_id INT NOT NULL,
  role_id INT NOT NULL,
  PRIMARY KEY (user_id, role_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

CREATE TABLE role_grants (
  role_id INT NOT NULL,
  domain VARCHAR(30) NOT NULL,
  scope VARCHAR(20) NOT NULL,
  PRIMARY KEY (role_id, domain, scope),
  FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

CREATE TABLE user_grants (
  user_id INT NOT NULL,
  domain VARCHAR(30) NOT NULL,
  scope VARCHAR(20) NOT NULL,
  PRIMARY KEY (user_id, domain, scope),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE user_groups (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  description VARCHAR(255) NOT NULL DEFAULT '',
  created_by INT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE group_members (
  group_id INT NOT NULL,
  user_id INT NOT NULL,
  added_by INT NULL,
  added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (group_id, user_id),
  INDEX idx_members_user (user_id),
  FOREIGN KEY (group_id) REFERENCES user_groups(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE group_grants (
  group_id INT NOT NULL,
  domain VARCHAR(30) NOT NULL,
  scope VARCHAR(20) NOT NULL,
  PRIMARY KEY (group_id, domain, scope),
  FOREIGN KEY (group_id) REFERENCES user_groups(id) ON DELETE CASCADE
);

CREATE TABLE access_audit_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  changed_by INT NULL,
  action VARCHAR(50) NOT NULL,
  target VARCHAR(150) NOT NULL,
  details VARCHAR(500) NOT NULL DEFAULT '',
  changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_audit_date (changed_at)
);
