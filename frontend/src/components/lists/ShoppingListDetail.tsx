import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../../services/api';

interface ListItem {
  id: number;
  name: string;
  quantity: number;
  unit?: string;
  is_completed: boolean;
  created_at: string;
  updated_at: string;
}

interface ShoppingList {
  id: number;
  title: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

const ShoppingListDetail: React.FC = () => {
  const { listId } = useParams<{ listId: string }>();
  const navigate = useNavigate();
  const [list, setList] = useState<ShoppingList | null>(null);
  const [items, setItems] = useState<ListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [newItem, setNewItem] = useState({
    name: '',
    quantity: 1,
    unit: '',
  });
  const [editingItem, setEditingItem] = useState<ListItem | null>(null);

  useEffect(() => {
    if (listId) {
      fetchList();
      fetchItems();
    }
  }, [listId]);

  const fetchList = async () => {
    try {
      const response = await apiClient.getShoppingList(parseInt(listId!));
      setList(response.data);
    } catch (err: any) {
      setError('Failed to load shopping list');
      console.error(err);
    }
  };

  const fetchItems = async () => {
    try {
      const response = await apiClient.getListItems(parseInt(listId!));
      setItems(response.data);
    } catch (err: any) {
      setError('Failed to load list items');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newItem.name.trim()) return;

    try {
      await apiClient.createListItem(parseInt(listId!), {
        name: newItem.name,
        quantity: newItem.quantity,
        unit: newItem.unit || undefined,
        is_completed: false,
      });
      setNewItem({ name: '', quantity: 1, unit: '' });
      fetchItems();
    } catch (err: any) {
      setError('Failed to add item');
      console.error(err);
    }
  };

  const handleToggleComplete = async (item: ListItem) => {
    try {
      await apiClient.updateListItem(parseInt(listId!), item.id, {
        is_completed: !item.is_completed,
      });
      fetchItems();
    } catch (err: any) {
      setError('Failed to update item');
      console.error(err);
    }
  };

  const handleEditItem = (item: ListItem) => {
    setEditingItem(item);
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingItem) return;

    try {
      await apiClient.updateListItem(parseInt(listId!), editingItem.id, {
        name: editingItem.name,
        quantity: editingItem.quantity,
        unit: editingItem.unit,
      });
      setEditingItem(null);
      fetchItems();
    } catch (err: any) {
      setError('Failed to update item');
      console.error(err);
    }
  };

  const handleDeleteItem = async (itemId: number) => {
    if (!confirm('Are you sure you want to delete this item?')) return;

    try {
      await apiClient.deleteListItem(parseInt(listId!), itemId);
      fetchItems();
    } catch (err: any) {
      setError('Failed to delete item');
      console.error(err);
    }
  };

  const handleDeleteList = async () => {
    if (!confirm('Are you sure you want to delete this entire list?')) return;

    try {
      await apiClient.deleteShoppingList(parseInt(listId!));
      navigate('/dashboard');
    } catch (err: any) {
      setError('Failed to delete list');
      console.error(err);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!list) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">List not found</h2>
          <button
            onClick={() => navigate('/dashboard')}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => navigate('/dashboard')}
                className="text-gray-600 hover:text-gray-900 mr-4"
              >
                ← Back
              </button>
              <h1 className="text-xl font-semibold text-gray-900">{list.title}</h1>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleDeleteList}
                className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-md text-sm font-medium"
              >
                Delete List
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Error message */}
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* List Description */}
          {list.description && (
            <div className="mb-6 bg-white rounded-lg shadow p-4">
              <p className="text-gray-600">{list.description}</p>
            </div>
          )}

          {/* Add New Item Form */}
          <div className="mb-6 bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Item</h3>
            <form onSubmit={handleAddItem} className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Item name"
                  value={newItem.name}
                  onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>
              <div className="w-full sm:w-24">
                <input
                  type="number"
                  placeholder="Qty"
                  value={newItem.quantity}
                  onChange={(e) => setNewItem({ ...newItem, quantity: parseFloat(e.target.value) || 1 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  min="0.1"
                  step="0.1"
                />
              </div>
              <div className="w-full sm:w-24">
                <input
                  type="text"
                  placeholder="Unit"
                  value={newItem.unit}
                  onChange={(e) => setNewItem({ ...newItem, unit: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <button
                type="submit"
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium whitespace-nowrap"
              >
                Add Item
              </button>
            </form>
          </div>

          {/* Items List */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Items ({items.length})</h3>
            </div>

            {items.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No items in this list yet. Add your first item above!
              </div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {items.map((item) => (
                  <li key={item.id} className="px-6 py-4">
                    {editingItem?.id === item.id ? (
                      <form onSubmit={handleSaveEdit} className="flex items-center space-x-4">
                        <input
                          type="text"
                          value={editingItem.name}
                          onChange={(e) => setEditingItem({ ...editingItem, name: e.target.value })}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                          required
                        />
                        <input
                          type="number"
                          value={editingItem.quantity}
                          onChange={(e) => setEditingItem({ ...editingItem, quantity: parseFloat(e.target.value) || 1 })}
                          className="w-20 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                          min="0.1"
                          step="0.1"
                        />
                        <input
                          type="text"
                          value={editingItem.unit || ''}
                          onChange={(e) => setEditingItem({ ...editingItem, unit: e.target.value })}
                          className="w-20 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                        />
                        <button
                          type="submit"
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-md text-sm"
                        >
                          Save
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditingItem(null)}
                          className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded-md text-sm"
                        >
                          Cancel
                        </button>
                      </form>
                    ) : (
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <input
                            type="checkbox"
                            checked={item.is_completed}
                            onChange={() => handleToggleComplete(item)}
                            className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                          />
                          <div className={`flex-1 ${item.is_completed ? 'line-through text-gray-500' : ''}`}>
                            <span className="font-medium">{item.name}</span>
                            <span className="ml-2 text-sm text-gray-600">
                              {item.quantity} {item.unit}
                            </span>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleEditItem(item)}
                            className="text-indigo-600 hover:text-indigo-900 text-sm"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteItem(item.id)}
                            className="text-red-600 hover:text-red-900 text-sm"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default ShoppingListDetail;