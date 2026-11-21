import { useId, type SelectHTMLAttributes } from "react";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: string[];
  placeholder?: string;
  hideLabel?: boolean;
}

export function Select({
  label,
  options,
  placeholder,
  hideLabel = false,
  id,
  ...rest
}: SelectProps) {
  const generatedId = useId();
  const selectId = id ?? generatedId;
  return (
    <div className="field">
      <label htmlFor={selectId} className={hideLabel ? "visually-hidden" : "field-label"}>
        {label}
      </label>
      <select id={selectId} className="input select" {...rest}>
        {placeholder !== undefined && <option value="">{placeholder}</option>}
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </div>
  );
}
