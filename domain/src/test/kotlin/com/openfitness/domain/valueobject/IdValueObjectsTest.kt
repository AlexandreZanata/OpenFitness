package com.openfitness.domain.valueobject

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test
import java.util.UUID

class IdValueObjectsTest {

    @Test
    fun `ExerciseId round trip`() {
        val id = ExerciseId.generate()
        assertEquals(id, ExerciseId.fromString(id.toString()))
    }

    @Test
    fun `SessionId round trip`() {
        val id = SessionId.generate()
        assertEquals(id, SessionId.fromString(id.toString()))
    }

    @Test
    fun `Duration from minutes`() {
        assertEquals(120L, Duration.fromMinutes(2).seconds)
    }

    @Test
    fun `TemplateId and SetLogId generate unique values`() {
        val t1 = TemplateId.generate()
        val t2 = TemplateId.generate()
        val s1 = SetLogId.generate()
        val s2 = SetLogId.generate()
        assertEquals(false, t1.value == t2.value)
        assertEquals(false, s1.value == s2.value)
    }
}
