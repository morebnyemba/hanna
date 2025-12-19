import Link from 'next/link';
import { FiEdit, FiTrash2, FiEye } from 'react-icons/fi';

interface ActionButtonsProps {
  entityId: number | string;
  editPath?: string;
  viewPath?: string;
  onDelete?: () => void;
  showView?: boolean;
  showEdit?: boolean;
  showDelete?: boolean;
}

export default function ActionButtons({
  entityId,
  editPath,
  viewPath,
  onDelete,
  showView = true,
  showEdit = true,
  showDelete = true,
}: ActionButtonsProps) {
  return (
    <div className="flex items-center gap-2">
      {showView && viewPath && (
        <Link href={viewPath}>
          <button
            className="p-2 text-blue-600 hover:bg-blue-50 rounded-md transition"
            title="View"
          >
            <FiEye className="w-4 h-4" />
          </button>
        </Link>
      )}
      {showEdit && editPath && (
        <Link href={editPath}>
          <button
            className="p-2 text-gray-600 hover:bg-gray-50 rounded-md transition"
            title="Edit"
          >
            <FiEdit className="w-4 h-4" />
          </button>
        </Link>
      )}
      {showDelete && onDelete && (
        <button
          onClick={onDelete}
          className="p-2 text-red-600 hover:bg-red-50 rounded-md transition"
          title="Delete"
        >
          <FiTrash2 className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
