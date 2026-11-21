import { useState, type FormEvent } from "react";
import { accessApi } from "../api/client";
import type { UserCreateRequest } from "../api/types";
import { Button, Card, Input } from "../components/ui";
import type { ActionRunner } from "./useAccessAction";

const EMPTY_FORM = {
  username: "",
  displayName: "",
  password: "",
  studentId: "",
  facultyId: "",
  deptId: "",
};

type FormValues = typeof EMPTY_FORM;

function optionalId(value: string): number | null {
  const trimmed = value.trim();
  return trimmed ? Number(trimmed) : null;
}

function toRequest(values: FormValues): UserCreateRequest {
  return {
    username: values.username.trim(),
    display_name: values.displayName.trim(),
    password: values.password,
    student_id: optionalId(values.studentId),
    faculty_id: optionalId(values.facultyId),
    dept_id: optionalId(values.deptId),
  };
}

export function CreateUserForm({ run }: { run: ActionRunner }) {
  const [values, setValues] = useState(EMPTY_FORM);
  const update = (field: keyof FormValues) => (event: { target: { value: string } }) =>
    setValues((current) => ({ ...current, [field]: event.target.value }));

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const request = toRequest(values);
    if (await run(() => accessApi.createUser(request), `Created user ${request.username}.`)) {
      setValues(EMPTY_FORM);
    }
  };

  const isComplete = values.username.trim() && values.displayName.trim() && values.password;

  return (
    <Card title="New user">
      <form className="form-grid" onSubmit={handleSubmit}>
        <Input label="Username" value={values.username} onChange={update("username")} required />
        <Input
          label="Display name"
          value={values.displayName}
          onChange={update("displayName")}
          required
        />
        <Input
          label="Password"
          type="password"
          minLength={6}
          value={values.password}
          onChange={update("password")}
          required
          autoComplete="new-password"
        />
        <Input
          label="Student ID"
          type="number"
          value={values.studentId}
          onChange={update("studentId")}
        />
        <Input
          label="Faculty ID"
          type="number"
          value={values.facultyId}
          onChange={update("facultyId")}
        />
        <Input
          label="Department ID"
          type="number"
          value={values.deptId}
          onChange={update("deptId")}
        />
        <Button type="submit" disabled={!isComplete}>
          Create user
        </Button>
      </form>
    </Card>
  );
}
