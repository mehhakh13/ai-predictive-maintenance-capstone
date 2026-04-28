import React, { useState, useMemo } from 'react';
import { Search, ChevronUp, ChevronDown } from 'lucide-react';
import { formatCurrency } from '../../utils/format';

const DefectTable = ({ data, onRowClick }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: 'WOStartDate', direction: 'desc' });
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // Filter data based on search
  const filteredData = useMemo(() => {
    if (!searchTerm) return data;

    const lowerSearch = searchTerm.toLowerCase();
    return data.filter(item =>
      item.WODescription.toLowerCase().includes(lowerSearch) ||
      item.defect_type.toLowerCase().includes(lowerSearch) ||
      item.SystemDescription.toLowerCase().includes(lowerSearch) ||
      item.BuildingName.toLowerCase().includes(lowerSearch)
    );
  }, [data, searchTerm]);

  // Sort data
  const sortedData = useMemo(() => {
    const sorted = [...filteredData];

    sorted.sort((a, b) => {
      let aVal = a[sortConfig.key];
      let bVal = b[sortConfig.key];

      // Handle dates
      if (sortConfig.key === 'WOStartDate') {
        aVal = new Date(aVal);
        bVal = new Date(bVal);
      }

      // Handle numbers
      if (sortConfig.key === 'TotalCost') {
        aVal = parseFloat(aVal);
        bVal = parseFloat(bVal);
      }

      if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [filteredData, sortConfig]);

  // Paginate data
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return sortedData.slice(startIndex, startIndex + itemsPerPage);
  }, [sortedData, currentPage]);

  const totalPages = Math.ceil(sortedData.length / itemsPerPage);

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const SortIcon = ({ columnKey }) => {
    if (sortConfig.key !== columnKey) return null;
    return sortConfig.direction === 'asc' ?
      <ChevronUp size={14} /> :
      <ChevronDown size={14} />;
  };

  return (
    <div className="defect-table-container">
      <div className="table-header">
        <h3>Work Order Details</h3>
        <div className="table-search">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search work orders..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
          />
        </div>
      </div>

      <div className="table-wrapper">
        <table className="defect-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('WODescription')}>
                Description <SortIcon columnKey="WODescription" />
              </th>
              <th onClick={() => handleSort('defect_type')}>
                Defect Type <SortIcon columnKey="defect_type" />
              </th>
              <th onClick={() => handleSort('SystemDescription')}>
                System <SortIcon columnKey="SystemDescription" />
              </th>
              <th onClick={() => handleSort('BuildingName')}>
                Building <SortIcon columnKey="BuildingName" />
              </th>
              <th onClick={() => handleSort('TotalCost')}>
                Cost <SortIcon columnKey="TotalCost" />
              </th>
              <th onClick={() => handleSort('WOStartDate')}>
                Date <SortIcon columnKey="WOStartDate" />
              </th>
            </tr>
          </thead>
          <tbody>
            {paginatedData.map(item => (
              <tr
                key={item.WOId}
                onClick={() => onRowClick && onRowClick(item)}
                className="table-row-clickable"
              >
                <td className="description-cell">{item.WODescription}</td>
                <td>{item.defect_type}</td>
                <td>{item.SystemDescription}</td>
                <td>{item.BuildingName}</td>
                <td className="cost-cell">{formatCurrency(item.TotalCost)}</td>
                <td>{new Date(item.WOStartDate).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ fontSize: '11px', color: '#64748b', padding: '8px 4px 0', fontStyle: 'italic' }}>
        * Cost figures are synthetic estimates based on defect type and priority — real cost data (DMC) is unavailable in the source dataset.
      </div>

      {totalPages > 1 && (
        <div className="table-pagination">
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
          >
            Previous
          </button>
          <span>
            Page {currentPage} of {totalPages} ({sortedData.length} results)
          </span>
          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default DefectTable;
