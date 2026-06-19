package com.openfitness.domain.rule

import com.openfitness.domain.exception.DomainException
import com.openfitness.domain.exception.ImmutableRecordException
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.Weight
import org.junit.jupiter.api.Assertions.assertDoesNotThrow
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test

class BusinessRulesTest {

    @Test
    fun `BR-003 GIVEN zero exercises WHEN validate THEN fails`() {
        assertThrows(DomainException::class.java) {
            SessionMustHaveExercisesRule().validate(0)
        }
    }

    @Test
    fun `BR-004 GIVEN no metrics WHEN validate THEN fails`() {
        assertThrows(DomainException::class.java) {
            CompletedSetRequiresMetricsRule().validate(null, null)
        }
    }

    @Test
    fun `BR-002 GIVEN valid metrics WHEN validate THEN passes`() {
        assertDoesNotThrow {
            PositiveSetValuesRule().validate(Weight.fromKilograms(40.0), RepCount(12))
        }
    }

    @Test
    fun `BR-007 GIVEN bundled WHEN validate mutation THEN fails`() {
        assertThrows(ImmutableRecordException::class.java) {
            BundledExerciseImmutabilityRule().validateMutation(isCustom = false)
        }
    }
}
