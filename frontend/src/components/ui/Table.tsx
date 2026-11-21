import { useVirtualizer } from "@tanstack/react-virtual";
import { memo, useRef, type ReactNode } from "react";
import {
  TABLE_ROW_HEIGHT_PX,
  TABLE_VIEWPORT_HEIGHT_PX,
  VIRTUALIZE_ROW_THRESHOLD,
} from "../../config";

interface TableProps {
  columns: string[];
  rows: ReactNode[][];
  caption?: string;
  highlightedRow?: number;
}

function TableHead({ columns }: { columns: string[] }) {
  return (
    <thead>
      <tr>
        {columns.map((column, index) => (
          <th key={`${column}-${index}`} scope="col">
            {column}
          </th>
        ))}
      </tr>
    </thead>
  );
}

interface TableRowProps {
  cells: ReactNode[];
  rowIndex: number;
  isHighlighted: boolean;
}

function TableRow({ cells, rowIndex, isHighlighted }: TableRowProps) {
  return (
    <tr data-row-index={rowIndex} className={isHighlighted ? "table-row--highlight" : undefined}>
      {cells.map((cell, index) => (
        <td key={index}>{cell}</td>
      ))}
    </tr>
  );
}

function SpacerRow({ height, columnCount }: { height: number; columnCount: number }) {
  if (height <= 0) return null;
  return (
    <tr aria-hidden="true" className="table-spacer">
      <td colSpan={columnCount} style={{ height }} />
    </tr>
  );
}

function VirtualTable({ columns, rows, caption, highlightedRow }: TableProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => TABLE_ROW_HEIGHT_PX,
    overscan: 10,
    initialRect: { width: 0, height: TABLE_VIEWPORT_HEIGHT_PX },
  });
  const items = virtualizer.getVirtualItems();
  const topSpace = items[0]?.start ?? 0;
  const bottomSpace = virtualizer.getTotalSize() - (items.at(-1)?.end ?? 0);

  return (
    <div
      ref={scrollRef}
      className="table-scroll table-scroll--virtual"
      style={{ maxHeight: TABLE_VIEWPORT_HEIGHT_PX }}
    >
      <table className="table">
        {caption && <caption className="visually-hidden">{caption}</caption>}
        <TableHead columns={columns} />
        <tbody>
          <SpacerRow height={topSpace} columnCount={columns.length} />
          {items.map((item) => (
            <TableRow
              key={item.key}
              cells={rows[item.index] ?? []}
              rowIndex={item.index}
              isHighlighted={item.index === highlightedRow}
            />
          ))}
          <SpacerRow height={bottomSpace} columnCount={columns.length} />
        </tbody>
      </table>
    </div>
  );
}

function PlainTable({ columns, rows, caption, highlightedRow }: TableProps) {
  return (
    <div className="table-scroll">
      <table className="table">
        {caption && <caption className="visually-hidden">{caption}</caption>}
        <TableHead columns={columns} />
        <tbody>
          {rows.map((cells, index) => (
            <TableRow
              key={index}
              cells={cells}
              rowIndex={index}
              isHighlighted={index === highlightedRow}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

export const Table = memo(function Table(props: TableProps) {
  if (props.rows.length > VIRTUALIZE_ROW_THRESHOLD) return <VirtualTable {...props} />;
  return <PlainTable {...props} />;
});
