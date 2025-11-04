'use client';

import { FiAlertTriangle, FiLoader, FiX } from 'react-icons/fi';

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  isConfirming: boolean;
}



export default function ConfirmationModal({ isOpen, onClose, onConfirm, title, message, isConfirming }: ConfirmationModalProps) {

  if (!isOpen) return null;



  return (

    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex justify-center items-center p-4">

      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">

        <div className="p-6">

          <div className="flex flex-col sm:flex-row items-center text-center sm:text-left">

            <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">

              <FiAlertTriangle className="h-6 w-6 text-red-600" aria-hidden="true" />

            </div>

            <div className="mt-3 sm:mt-0 sm:ml-4">

              <h3 className="text-lg leading-6 font-medium text-gray-900">{title}</h3>

              <div className="mt-2">

                <p className="text-sm text-gray-500">{message}</p>

              </div>

            </div>

          </div>

        </div>

        <div className="bg-gray-50 px-4 py-3 sm:px-6 flex flex-col-reverse sm:flex-row sm:justify-end gap-2 rounded-b-lg">

          <button type="button" onClick={onConfirm} disabled={isConfirming} className="w-full sm:w-auto inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:text-sm disabled:opacity-50">

            {isConfirming ? <FiLoader className="animate-spin" /> : 'Delete'}

          </button>

          <button type="button" onClick={onClose} disabled={isConfirming} className="w-full sm:w-auto inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:text-sm disabled:opacity-50">

            Cancel

          </button>

        </div>

      </div>

    </div>

  );

}
