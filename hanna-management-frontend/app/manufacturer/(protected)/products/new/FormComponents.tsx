import React from 'react';

export const InputField = ({ id, label, value, onChange, required = false, type = 'text', placeholder = '', error }: { id: string; label: string; value: string; onChange: (e: React.ChangeEvent<HTMLInputElement>) => void; required?: boolean; type?: string; placeholder?: string; error?: string; }) => (
    <div>
        <label htmlFor={id} className="block text-sm font-medium text-gray-700">{label}</label>
        <input
            type={type}
            id={id}
            name={id}
            value={value}
            onChange={onChange}
            required={required}
            placeholder={placeholder}
            className={`mt-1 block w-full px-4 py-3 bg-white border ${error ? 'border-red-500' : 'border-gray-300'} rounded-xl shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm transition-all duration-300`}
        />
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
);

export const SelectField = ({ id, label, value, onChange, children, error }: { id: string; label: string; value: string; onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void; children: React.ReactNode; error?: string; }) => (
    <div>
        <label htmlFor={id} className="block text-sm font-medium text-gray-700">{label}</label>
        <select
            id={id}
            name={id}
            value={value}
            onChange={onChange}
            className={`mt-1 block w-full px-4 py-3 bg-white border ${error ? 'border-red-500' : 'border-gray-300'} rounded-xl shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm transition-all duration-300`}
        >
            {children}
        </select>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
);

export const TextAreaField = ({ id, label, value, onChange, required = false, placeholder = '', error }: { id: string; label: string; value: string; onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void; required?: boolean; placeholder?: string; error?: string; }) => (
    <div>
        <label htmlFor={id} className="block text-sm font-medium text-gray-700">{label}</label>
        <textarea
            id={id}
            name={id}
            value={value}
            onChange={onChange}
            required={required}
            placeholder={placeholder}
            rows={3}
            className={`mt-1 block w-full px-4 py-3 bg-white border ${error ? 'border-red-500' : 'border-gray-300'} rounded-xl shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm transition-all duration-300`}
        />
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
);
