import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

export interface DataColumn<Row> {
  className?: string;
  header: string;
  render: (row: Row) => ReactNode;
}

interface DataTableProps<Row> {
  columns: DataColumn<Row>[];
  containerClassName?: string;
  getRowKey: (row: Row) => string;
  rows: Row[];
}

export function DataTable<Row>({
  columns,
  containerClassName,
  getRowKey,
  rows,
}: DataTableProps<Row>): ReactNode {
  return (
    <div
      className={cn(
        'overflow-hidden rounded-md border border-slate-200 bg-white',
        containerClassName,
      )}
    >
      <table className="w-full table-fixed border-collapse">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
          <tr>
            {columns.map((column) => (
              <th
                className={cn(
                  'border-b border-slate-200 px-4 py-3',
                  column.className,
                )}
                key={column.header}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200 text-sm">
          {rows.map((row) => (
            <tr
              className="bg-white transition hover:bg-slate-50"
              key={getRowKey(row)}
            >
              {columns.map((column) => (
                <td
                  className={cn('px-4 py-4 align-middle', column.className)}
                  key={column.header}
                >
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
