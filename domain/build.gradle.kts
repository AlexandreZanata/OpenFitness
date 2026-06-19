plugins {
    alias(libs.plugins.kotlin.jvm)
    jacoco
}

kotlin {
    jvmToolchain(17)
}

dependencies {
    implementation(libs.kotlinx.coroutines.core)

    testImplementation(libs.junit.jupiter)
    testImplementation(libs.mockk)
}

tasks.test {
    useJUnitPlatform()
    finalizedBy(tasks.jacocoTestReport)
}

tasks.jacocoTestReport {
    dependsOn(tasks.test)
    reports {
        xml.required.set(true)
        html.required.set(true)
    }
}

tasks.jacocoTestCoverageVerification {
    dependsOn(tasks.jacocoTestReport)
    classDirectories.setFrom(
        files(classDirectories.files.map { directory ->
            fileTree(directory) {
                exclude(
                    "**/repository/**",
                    "**/event/**",
                    "**/valueobject/MuscleGroup*",
                    "**/valueobject/EquipmentType*",
                    "**/valueobject/SessionStatus*",
                    "**/valueobject/PersonalRecordMetric*",
                    "**/model/PersonalRecordHistoryEntry*",
                    "**/model/PersonalRecordCandidate*",
                )
            }
        }),
    )
    violationRules {
        rule {
            limit {
                minimum = "0.90".toBigDecimal()
            }
        }
    }
}

tasks.check {
    dependsOn(tasks.jacocoTestCoverageVerification)
}
