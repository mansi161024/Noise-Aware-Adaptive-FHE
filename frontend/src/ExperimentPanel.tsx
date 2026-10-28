import { useState } from 'react';

interface ExperimentResult {
    strategy: string;
    input_data: number[];
    operations: number;
    threshold?: number;
    expected_values: number[];
    decrypted_values: number[];
    maximum_absolute_error: number;
    final_ciphertext_level: number;
    bootstrap_count: number;
    total_bootstrap_time: number;
    total_execution_time: number;
    operation_data?: OperationData[];
}

interface OperationData {
    operation: number;
    ciphertext_level: number;
    operations_since_bootstrap: number;
    decision: string;
    bootstrap_time: number;
}

const ExperimentPanel = () => {
    const [inputData, setInputData] = useState('0.1, 0.2, 0.3, 0.4');

    const [operations, setOperations] = useState(4);

    const [strategy, setStrategy] = useState('adaptive');

    const [threshold, setThreshold] = useState(2);

    const [fixedPoint, setFixedPoint] = useState(2);

    const [result, setResult] = useState<ExperimentResult | null>(null);

    const [loading, setLoading] = useState(false);

    const runExperiment = async () => {

        setLoading(true);
        setResult(null);

        try {

            const values = inputData
                .split(',')
                .map(value => Number(value.trim()))
                .filter(value => !Number.isNaN(value));

            const response = await fetch(
                'http://127.0.0.1:8000/api/experiments/run',
                {
                    method: 'POST',

                    headers: {
                        'Content-Type': 'application/json'
                    },

                    body: JSON.stringify({
                        strategy,
                        input_data: values,
                        operations,
                        threshold,
                        fixed_bootstrap_after: fixedPoint
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || 'Experiment failed'
                );
            }

            setResult(data.result);

        } catch (error) {

            console.error(error);

            alert(
                error instanceof Error
                    ? error.message
                    : 'Experiment failed'
            );

        } finally {

            setLoading(false);

        }
    };

    return (
        <div className="experiment-page">

            <div className="header">

                <div>
                    <h1>Run FHE Experiment</h1>

                    <p>
                        Execute a real CKKS homomorphic encryption experiment
                    </p>
                </div>

            </div>


            {/* Configuration */}

            <div className="glass-panel">

                <div className="panel-header">

                    <div className="panel-title">
                        Experiment Configuration
                    </div>

                </div>


                <div className="form-group">

                    <label>
                        Input Data
                    </label>

                    <input
                        value={inputData}
                        onChange={(e) =>
                            setInputData(e.target.value)
                        }
                        placeholder="0.1, 0.2, 0.3, 0.4"
                    />

                </div>


                <div className="form-group">

                    <label>
                        Number of Operations
                    </label>

                    <input
                        type="number"
                        min="1"
                        max="20"
                        value={operations}
                        onChange={(e) =>
                            setOperations(Number(e.target.value))
                        }
                    />

                </div>


                <div className="form-group">

                    <label>
                        Bootstrapping Strategy
                    </label>

                    <div className="strategy-options">

                        <label>

                            <input
                                type="radio"
                                value="none"
                                checked={strategy === 'none'}
                                onChange={(e) =>
                                    setStrategy(e.target.value)
                                }
                            />

                            No Bootstrapping

                        </label>


                        <label>

                            <input
                                type="radio"
                                value="fixed"
                                checked={strategy === 'fixed'}
                                onChange={(e) =>
                                    setStrategy(e.target.value)
                                }
                            />

                            Fixed Bootstrapping

                        </label>


                        <label>

                            <input
                                type="radio"
                                value="adaptive"
                                checked={strategy === 'adaptive'}
                                onChange={(e) =>
                                    setStrategy(e.target.value)
                                }
                            />

                            Adaptive Bootstrapping

                        </label>

                    </div>

                </div>


                {strategy === 'adaptive' && (

                    <div className="form-group">

                        <label>
                            Adaptive Threshold
                        </label>

                        <input
                            type="number"
                            min="1"
                            value={threshold}
                            onChange={(e) =>
                                setThreshold(Number(e.target.value))
                            }
                        />

                    </div>

                )}


                {strategy === 'fixed' && (

                    <div className="form-group">

                        <label>
                            Bootstrap After Operation
                        </label>

                        <input
                            type="number"
                            min="1"
                            value={fixedPoint}
                            onChange={(e) =>
                                setFixedPoint(Number(e.target.value))
                            }
                        />

                    </div>

                )}


                <button
                    className="btn"
                    onClick={runExperiment}
                    disabled={loading}
                >

                    {loading
                        ? 'Running OpenFHE Experiment...'
                        : 'Run Experiment'}

                </button>

            </div>


            {/* Results */}

            {result && (

                <>

                    <div className="grid">

                        <div className="card">

                            <div className="card-title">
                                Strategy
                            </div>

                            <div className="card-value">
                                {result.strategy}
                            </div>

                        </div>


                        <div className="card">

                            <div className="card-title">
                                Execution Time
                            </div>

                            <div className="card-value">
                                {result.total_execution_time.toFixed(3)}s
                            </div>

                        </div>


                        <div className="card">

                            <div className="card-title">
                                Bootstrap Count
                            </div>

                            <div className="card-value">
                                {result.bootstrap_count}
                            </div>

                        </div>


                        <div className="card">

                            <div className="card-title">
                                Maximum Absolute Error
                            </div>

                            <div className="card-value">
                                {result.maximum_absolute_error.toExponential(3)}
                            </div>

                        </div>

                    </div>


                    <div className="glass-panel">

                        <div className="panel-title">
                            Experiment Results
                        </div>

                        <p>
                            <strong>Input:</strong>{' '}
                            {result.input_data.join(', ')}
                        </p>

                        <p>
                            <strong>Expected:</strong>{' '}
                            {result.expected_values
                                .map(v => v.toExponential(4))
                                .join(', ')}
                        </p>

                        <p>
                            <strong>Decrypted:</strong>{' '}
                            {result.decrypted_values
                                .map(v => v.toExponential(4))
                                .join(', ')}
                        </p>

                        <p>
                            <strong>Final Ciphertext Level:</strong>{' '}
                            {result.final_ciphertext_level}
                        </p>

                        <p>
                            <strong>Total Bootstrap Time:</strong>{' '}
                            {result.total_bootstrap_time.toFixed(3)}s
                        </p>

                    </div>


                    {/* Operation table */}

                    {result.operation_data && (

                        <div className="glass-panel">

                            <div className="panel-title">
                                Operation Analysis
                            </div>

                            <table>

                                <thead>

                                    <tr>
                                        <th>Operation</th>
                                        <th>Ciphertext Level</th>
                                        <th>Operations Since Bootstrap</th>
                                        <th>Decision</th>
                                        <th>Bootstrap Time</th>
                                    </tr>

                                </thead>

                                <tbody>

                                    {result.operation_data.map(
                                        (operation) => (

                                            <tr key={operation.operation}>

                                                <td>
                                                    {operation.operation}
                                                </td>

                                                <td>
                                                    {operation.ciphertext_level}
                                                </td>

                                                <td>
                                                    {operation.operations_since_bootstrap}
                                                </td>

                                                <td>
                                                    {operation.decision}
                                                </td>

                                                <td>
                                                    {operation.bootstrap_time.toFixed(3)}s
                                                </td>

                                            </tr>

                                        )
                                    )}

                                </tbody>

                            </table>

                        </div>

                    )}

                </>

            )}

        </div>
    );
};

export default ExperimentPanel;