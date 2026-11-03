from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pandas as pd
import numpy as np
from residual_experiment import residual_target,combine_predictions

def test_residual_reconstruction_preserves_original_target_and_missingness():
    panel=pd.DataFrame({'target_log_return':[.1,np.nan,-.1],'return_6':[.08,.04,.02]})
    transformed=residual_target(panel)
    restored=transformed.target_log_return+.5*panel.return_6
    np.testing.assert_allclose(restored,panel.target_log_return,equal_nan=True)
    assert panel.target_log_return.iloc[0]==.1

def test_zero_residual_reduces_to_existing_damped_momentum_rule():
    predicted=combine_predictions(np.array([0.]),np.array([.1]))
    assert np.isclose(predicted[0],100*np.expm1(.05))

def test_residual_is_combined_in_log_space():
    predicted=combine_predictions(np.array([10.]),np.array([.2]))
    assert np.isclose(predicted[0],100*(1.1*np.exp(.1)-1))
