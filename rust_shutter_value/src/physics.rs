//! Port of the utility functions defined at the top of create_shutter_value_file_step1.py
//! (these use the rounded 0.3956 coefficient, like the Python script).

use crate::shutter::COEFF_STEP1;

/// lambda (Angstroms) -> TOF (microseconds)
pub fn from_lambda_to_tof(lambda: f64, detector_offset_us: f64, detector_sample_distance_m: f64) -> f64 {
    let coeff = (detector_sample_distance_m * 100.0) / COEFF_STEP1;
    lambda * coeff - detector_offset_us
}

/// detector offset (microseconds) for the minimum measurable lambda
pub fn convert_lambda_into_offset(lambda: f64, detector_sample_distance_m: f64) -> f64 {
    let coeff = (detector_sample_distance_m * 100.0) / COEFF_STEP1;
    lambda * coeff
}

/// TOF (microseconds) -> lambda (Angstroms)
pub fn from_tof_to_lambda(tof_us: f64, detector_offset_us: f64, detector_sample_distance_m: f64) -> f64 {
    let coeff = (detector_sample_distance_m * 100.0) / COEFF_STEP1;
    (tof_us + detector_offset_us) / coeff
}

/// The N largest consecutive gaps of a sorted list, largest first.
pub fn find_largest_gaps(data: &[f64], number_of_gaps: usize) -> Vec<f64> {
    let mut gaps: Vec<f64> = data.windows(2).map(|w| w[1] - w[0]).collect();
    gaps.sort_by(|a, b| b.partial_cmp(a).unwrap());
    gaps.truncate(number_of_gaps);
    gaps
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn offset_matches_python_defaults() {
        // step1 defaults: lambda 1.9 A, distance 25 m -> 1.9 * 2500 / 0.3956 us
        let offset = convert_lambda_into_offset(1.9, 25.0);
        assert!((offset - 1.9 * 2500.0 / 0.3956).abs() < 1e-9);
    }

    #[test]
    fn roundtrip() {
        let offset = convert_lambda_into_offset(1.9, 25.0);
        let tof = from_lambda_to_tof(3.5, offset, 25.0);
        let lam = from_tof_to_lambda(tof, offset, 25.0);
        assert!((lam - 3.5).abs() < 1e-9);
    }

    #[test]
    fn largest_gaps() {
        let data = [1.0, 2.0, 5.0, 5.5, 9.0];
        let gaps = find_largest_gaps(&data, 2);
        assert_eq!(gaps, vec![3.5, 3.0]);
    }
}
