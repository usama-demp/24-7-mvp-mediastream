// src/pages/Users.jsx
import { useState, useEffect } from "react";
import toast, { Toaster } from "react-hot-toast";
import {
  fetchUsers,
  createUser,
  updateUser,
  deleteUser as deleteUserAPI,
} from "../services/api";

export default function Users() {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({ username: "", email: "", role: "user", password: "" });
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [deleteUser, setDeleteUser] = useState(null);

  // Fetch users
  const loadUsers = async () => {
    try {
      const data = await fetchUsers();
      setUsers(data);
    } catch (err) {
      toast.error(err.message);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const openForm = (user = null) => {
    if (user) setForm({ ...user, password: "" }); // don't show password
    else setForm({ username: "", email: "", role: "user", password: "" });
    setIsFormOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (form.id) {
        await updateUser(form.id, form);
        toast.success("User updated successfully!");
      } else {
        await createUser(form);
        toast.success("User created successfully!");
      }
      setIsFormOpen(false);
      loadUsers();
    } catch (err) {
      toast.error(err.message);
    }
  };

  const handleDeleteClick = (user) => setDeleteUser(user);

  const confirmDelete = async () => {
    try {
      await deleteUserAPI(deleteUser.id);
      toast.success("User deleted successfully!");
      setDeleteUser(null);
      loadUsers();
    } catch (err) {
      toast.error(err.message);
    }
  };

  return (
    <div>
      <Toaster position="top-right" />
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Users</h1>
        <button
          onClick={() => openForm()}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Add User
        </button>
      </div>

      {/* Users Table */}
      <div className="overflow-x-auto bg-white shadow rounded">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Username</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {users.map((u) => (
              <tr key={u.id}>
                <td className="px-6 py-4">{u.username}</td>
                <td className="px-6 py-4">{u.email}</td>
                <td className="px-6 py-4">{u.role}</td>
                <td className="px-6 py-4 space-x-2">
                  <button onClick={() => openForm(u)} className="text-blue-600 hover:underline">Edit</button>
                  <button onClick={() => handleDeleteClick(u)} className="text-red-600 hover:underline">Delete</button>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td colSpan="4" className="text-center py-4 text-gray-500">No users found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal Form */}
      {isFormOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex justify-center items-center z-50">
          <div className="bg-white rounded p-6 w-full max-w-md shadow-lg">
            <h2 className="text-xl font-bold mb-4">{form.id ? "Edit User" : "Add User"}</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block mb-1">Username</label>
                <input
                  name="username"
                  value={form.username}
                  onChange={handleChange}
                  className="w-full border px-3 py-2 rounded"
                  required
                />
              </div>
              <div>
                <label className="block mb-1">Email</label>
                <input
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  className="w-full border px-3 py-2 rounded"
                  required
                />
              </div>
              <div>
                <label className="block mb-1">Password</label>
                <input
                  type="password"
                  name="password"
                  value={form.password}
                  onChange={handleChange}
                  className="w-full border px-3 py-2 rounded"
                  placeholder={form.id ? "Leave blank to keep unchanged" : ""}
                  required={!form.id}
                />
              </div>
              <div>
                <label className="block mb-1">Role</label>
                <select
                  name="role"
                  value={form.role}
                  onChange={handleChange}
                  className="w-full border px-3 py-2 rounded"
                >
                  <option value="admin">Admin</option>
                  <option value="user">User</option>
                </select>
              </div>
              <div className="flex justify-end space-x-2">
                <button type="button" onClick={() => setIsFormOpen(false)} className="px-4 py-2 rounded border">Cancel</button>
                <button type="submit" className="px-4 py-2 rounded bg-blue-500 text-white hover:bg-blue-600">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteUser && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex justify-center items-center z-50">
          <div className="bg-white rounded p-6 w-full max-w-sm shadow-lg text-center">
            <h2 className="text-xl font-bold mb-4">Confirm Delete</h2>
            <p className="mb-6">Are you sure you want to delete <strong>{deleteUser.username}</strong>?</p>
            <div className="flex justify-center space-x-4">
              <button onClick={() => setDeleteUser(null)} className="px-4 py-2 rounded border">Cancel</button>
              <button onClick={confirmDelete} className="px-4 py-2 rounded bg-red-500 text-white hover:bg-red-600">Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}